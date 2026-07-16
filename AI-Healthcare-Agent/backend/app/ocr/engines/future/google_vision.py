import hashlib
import time
from io import BytesIO
from typing import Optional

from PIL import Image

from app.ocr.base_ocr import BaseOCR
from app.ocr.config import OCRConfig
from app.ocr.ocr_factory import OCRFactory
from app.ocr.schemas import OcrBlock, OcrResult, OcrWord


class GoogleVisionEngine(BaseOCR):
    name = "google_vision"

    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()

    def process_image(self, image: Image.Image, language: str = "en") -> OcrResult:
        raise NotImplementedError(
            "Google Vision OCR engine is not yet implemented. "
            "Implement process_image() to enable Google Vision support. "
            "Use GOOGLE_APPLICATION_CREDENTIALS for authentication."
        )

    def _mock_process(self, image: Image.Image, language: str = "en") -> OcrResult:
        start = time.time()
        w, h = image.size

        raw = self._image_to_bytes(image)
        text = self._mock_ocr_text(raw, w, h)

        elapsed = (time.time() - start) * 1000

        words = [
            OcrWord(text=token, confidence=round(0.85 + abs(hash(token) % 10) / 100, 2))
            for token in text.split()
            if token.strip()
        ]

        words = words[:50]

        block = OcrBlock(
            text=text,
            confidence=0.92,
            block_type="text",
            words=words,
        )

        overall_conf = round(sum(w.confidence for w in words) / max(len(words), 1), 4) if words else 0.92

        return OcrResult(
            full_text=text,
            confidence=overall_conf,
            provider=f"{self.name}_mock",
            pages=[],
            blocks=[block],
            language=language,
            processing_time_ms=round(elapsed, 2),
        )

    def _mock_ocr_text(self, image_bytes: bytes, width: int, height: int) -> str:
        seed = int(hashlib.md5(image_bytes).hexdigest()[:8], 16) % 1000

        tokens_by_seed = [
            ["Patient", "Name:", "John", "Doe", "Date:", "2024-01-15",
             "Diagnosis:", "Hypertension", "Stage", "2",
             "Medications:", "Lisinopril", "10mg", "once", "daily",
             "Lab", "Results:", "BP:", "145/95", "mmHg",
             "Notes:", "Follow-up", "in", "2", "weeks."],
            ["Patient:", "Jane", "Smith", "DOB:", "1990-05-20",
             "Diagnosis:", "Type", "2", "Diabetes",
             "Medications:", "Metformin", "500mg", "twice", "daily",
             "HbA1c:", "7.2", "%", "Glucose:", "126", "mg/dL",
             "Dr.", "Brown", "Endocrinology"],
            ["Name:", "Robert", "Johnson", "Date:", "2024-03-01",
             "Diagnosis:", "Asthma",
             "Medications:", "Albuterol", "90mcg", "as", "needed",
             "Fluticasone", "250mcg", "daily",
             "Peak", "Flow:", "320", "L/min",
             "Notes:", "Stable", "condition"],
        ]

        sample_tokens = tokens_by_seed[seed % len(tokens_by_seed)]
        lines: list[str] = []
        current_line: list[str] = []
        avg_char_width = width / 80 if width > 0 else 8
        line_width = 0

        for token in sample_tokens:
            tok_width = len(token) * avg_char_width
            if line_width + tok_width > width * 0.9 and current_line:
                lines.append(" ".join(current_line))
                current_line = []
                line_width = 0
            current_line.append(token)
            line_width += tok_width + avg_char_width

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    @staticmethod
    def _image_to_bytes(image: Image.Image, fmt: str = "PNG") -> bytes:
        buf = BytesIO()
        image.save(buf, format=fmt)
        return buf.getvalue()


OCRFactory.register("google_vision", GoogleVisionEngine)
