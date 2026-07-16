import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from PIL import Image

from app.ocr.schemas import OcrPageResult, OcrResult


class BaseOCR(ABC):
    name: str = "base"

    @abstractmethod
    def process_image(self, image: Image.Image, language: str = "en") -> OcrResult:
        """Process a single image and return OCR results."""

    def process_pdf(self, pdf_path: Path, language: str = "en", dpi: int = 300) -> OcrResult:
        from app.ocr.preprocessor import ImagePreprocessor

        start = time.time()
        images = ImagePreprocessor.pdf_to_images(pdf_path, dpi=dpi)
        pages: list[OcrPageResult] = []
        full_text_parts: list[str] = []
        total_conf = 0.0

        for i, img in enumerate(images):
            page_result = self.process_image(img, language=language)
            pages.append(
                OcrPageResult(
                    page_number=i + 1,
                    text=page_result.full_text,
                    confidence=page_result.confidence,
                    language=language,
                    processing_time_ms=page_result.processing_time_ms,
                )
            )
            full_text_parts.append(page_result.full_text)
            total_conf += page_result.confidence

        avg_conf = total_conf / max(len(images), 1)
        elapsed = (time.time() - start) * 1000

        return OcrResult(
            full_text="\n\n".join(full_text_parts),
            confidence=round(avg_conf, 4),
            provider=self.name,
            pages=pages,
            language=language,
            processing_time_ms=round(elapsed, 2),
            has_more_pages=False,
        )
