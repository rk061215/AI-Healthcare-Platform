import time
from pathlib import Path
from typing import Optional

from PIL import Image

from app.core.config import settings
from app.ocr.base_ocr import BaseOCR
from app.ocr.config import OCRConfig
from app.ocr.ocr_factory import OCRFactory
from app.ocr.preprocessor import ImagePreprocessor
from app.ocr.schemas import OcrJobResult, OcrResult
from app.ocr.structured_extractor import extract_structured_data


class OcrEngine:
    def __init__(self, use_mock: bool = False):
        self.primary: Optional[BaseOCR] = None
        self.fallback: Optional[BaseOCR] = None
        self.preprocessor = ImagePreprocessor()
        self._init_providers(use_mock)

    def _init_providers(self, use_mock: bool = False) -> None:
        ocr_config = OCRConfig()
        primary_name = settings.OCR_PRIMARY_PROVIDER
        if primary_name == "tesseract":
            self.primary = OCRFactory.create("tesseract", ocr_config, use_mock=use_mock)
        else:
            self.primary = OCRFactory.create("google_vision", ocr_config)

        fallback_name = settings.OCR_FALLBACK_PROVIDER
        if fallback_name == "tesseract" and primary_name != "tesseract":
            self.fallback = OCRFactory.create("tesseract", ocr_config, use_mock=use_mock)
        elif fallback_name == "google_vision" and primary_name != "google_vision":
            self.fallback = OCRFactory.create("google_vision", ocr_config)

    def process_document(
        self,
        file_path: Path,
        file_type: str,
        retry_count: int = 0,
    ) -> OcrJobResult:
        start = time.time()
        result = self._execute_with_retry(file_path, file_type, retry_count)
        elapsed = (time.time() - start) * 1000
        result.processing_time_ms = round(elapsed, 2)
        return result

    def _execute_with_retry(
        self,
        file_path: Path,
        file_type: str,
        initial_retry_count: int = 0,
    ) -> OcrJobResult:
        from loguru import logger as llog

        max_attempts = settings.OCR_RETRY_MAX_ATTEMPTS
        backoff = settings.OCR_RETRY_BACKOFF_SECONDS
        threshold = settings.OCR_MIN_CONFIDENCE
        use_mock = settings.OCR_USE_MOCK

        llog.info(f"[OCR AUDIT] _execute_with_retry — file_type={file_type}, max_attempts={max_attempts}, threshold={threshold}, use_mock={use_mock}")
        llog.info(f"[OCR AUDIT] primary={self.primary.name if self.primary else None}, fallback={self.fallback.name if self.fallback else None}")

        for attempt in range(max_attempts):
            llog.info(f"[OCR AUDIT] === Attempt {attempt + 1}/{max_attempts} ===")
            try:
                provider = self.primary if attempt == 0 else (self.fallback or self.primary)
                llog.info(f"[OCR AUDIT] Using provider={provider.name}, attempt={attempt}")
                ocr_result, job_result = self._run_ocr(file_path, file_type, provider)
                job_result.retry_count = initial_retry_count + attempt
                llog.info(f"[OCR AUDIT] OCR completed — raw_confidence={ocr_result.confidence}, final_confidence={job_result.confidence}, text_length={job_result.text_length}, status={job_result.status}, provider={ocr_result.provider}")
                if job_result.full_text:
                    llog.info(f"[OCR AUDIT] Extracted text first 500 chars: {job_result.full_text[:500]!r}")
                else:
                    llog.warning(f"[OCR AUDIT] Extracted text is EMPTY")

                llog.info(f"[OCR AUDIT] Checking confidence: {job_result.confidence} >= {threshold} = {job_result.confidence >= threshold}")
                if job_result.confidence >= threshold:
                    llog.info(f"[OCR AUDIT] Confidence PASSED — returning result on attempt {attempt + 1}")
                    return job_result

                llog.info(f"[OCR AUDIT] Confidence BELOW threshold — checking fallback")
                if self.fallback and provider is not self.fallback:
                    llog.info(f"[OCR AUDIT] Trying fallback provider={self.fallback.name}")
                    fb_ocr, fb_job = self._run_ocr(file_path, file_type, self.fallback)
                    fb_job.retry_count = initial_retry_count + attempt + 1
                    llog.info(f"[OCR AUDIT] Fallback result — confidence={fb_job.confidence}, text_length={fb_job.text_length}")
                    if fb_job.confidence > job_result.confidence:
                        llog.info(f"[OCR AUDIT] Fallback confidence BETTER ({fb_job.confidence} > {job_result.confidence}) — returning fallback result")
                        return fb_job
                    else:
                        llog.info(f"[OCR AUDIT] Fallback confidence NOT better ({fb_job.confidence} <= {job_result.confidence})")
                else:
                    llog.info(f"[OCR AUDIT] No fallback available (primary={self.primary.name if self.primary else None}, fallback={self.fallback.name if self.fallback else None})")

                if attempt < max_attempts - 1:
                    sleep_time = backoff * (2 ** attempt)
                    llog.info(f"[OCR AUDIT] Retrying in {sleep_time}s (attempt {attempt + 1}/{max_attempts})")
                    import time as time_mod
                    time_mod.sleep(sleep_time)

            except Exception as e:
                llog.error(f"[OCR AUDIT] Attempt {attempt + 1} threw exception: {type(e).__name__}: {e}")
                if attempt >= max_attempts - 1:
                    llog.warning(f"[OCR AUDIT] Last attempt failed — returning failed result with exception")
                    return OcrJobResult(
                        report_id=file_path.stem,
                        status="failed",
                        provider=self.primary.name if self.primary else "unknown",
                        confidence=0.0,
                        pages_processed=0,
                        text_length=0,
                        processing_time_ms=0.0,
                        retry_count=initial_retry_count + attempt,
                        error_message=str(e),
                    )
                sleep_time = backoff * (2 ** attempt)
                llog.info(f"[OCR AUDIT] Exception not fatal — retrying in {sleep_time}s")
                import time as time_mod
                time_mod.sleep(sleep_time)

        llog.warning(f"[OCR AUDIT] All {max_attempts} attempts exhausted — returning 'Max retries exceeded with low confidence'")
        return OcrJobResult(
            report_id=file_path.stem,
            status="failed",
            provider=self.primary.name if self.primary else "unknown",
            confidence=0.0,
            pages_processed=0,
            text_length=0,
            processing_time_ms=0.0,
            retry_count=initial_retry_count + max_attempts - 1,
            error_message="Max retries exceeded with low confidence",
        )

    def _run_ocr(
        self, file_path: Path, file_type: str, provider: BaseOCR
    ) -> tuple[OcrResult, OcrJobResult]:
        ext = file_type.lower()
        preproc_info: dict = {"steps": [], "original_size": None, "final_size": None}

        if ext == "pdf":
            ocr_result = provider.process_pdf(file_path, dpi=settings.OCR_IMAGE_DPI)
        else:
            image = Image.open(file_path)
            if settings.OCR_PREPROCESS_ENABLE:
                processed, preproc_info = self.preprocessor.preprocess_image(image)
            else:
                processed = image
                preproc_info = {
                    "steps": [],
                    "original_size": image.size,
                    "final_size": processed.size,
                }
            ocr_result = provider.process_image(processed)

        structured = extract_structured_data(ocr_result.full_text)

        job_result = OcrJobResult(
            report_id=file_path.stem,
            status="completed",
            provider=ocr_result.provider,
            confidence=ocr_result.confidence,
            pages_processed=len(ocr_result.pages) if ocr_result.pages else 1,
            text_length=len(ocr_result.full_text),
            full_text=ocr_result.full_text,
            extracted_data=structured,
            preprocessing_applied=preproc_info if preproc_info.get("steps") else None,
            processing_time_ms=ocr_result.processing_time_ms,
            retry_count=0,
        )

        return ocr_result, job_result
