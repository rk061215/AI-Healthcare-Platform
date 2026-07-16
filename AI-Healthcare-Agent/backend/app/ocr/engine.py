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
        max_attempts = settings.OCR_RETRY_MAX_ATTEMPTS
        backoff = settings.OCR_RETRY_BACKOFF_SECONDS

        for attempt in range(max_attempts):
            try:
                provider = self.primary if attempt == 0 else (self.fallback or self.primary)
                ocr_result, job_result = self._run_ocr(file_path, file_type, provider)
                job_result.retry_count = initial_retry_count + attempt

                if job_result.confidence >= settings.OCR_MIN_CONFIDENCE:
                    return job_result

                if self.fallback and provider is not self.fallback:
                    fb_ocr, fb_job = self._run_ocr(file_path, file_type, self.fallback)
                    fb_job.retry_count = initial_retry_count + attempt + 1
                    if fb_job.confidence > job_result.confidence:
                        return fb_job

                if attempt < max_attempts - 1:
                    import time as time_mod
                    time_mod.sleep(backoff * (2 ** attempt))

            except Exception as e:
                if attempt >= max_attempts - 1:
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
                import time as time_mod
                time_mod.sleep(backoff * (2 ** attempt))

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
