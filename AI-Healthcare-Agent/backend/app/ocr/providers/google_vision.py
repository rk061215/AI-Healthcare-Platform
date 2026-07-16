import time
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from app.core.config import settings
from app.ocr.providers.base import OCRProvider
from app.ocr.schemas import OcrBlock, OcrResult, OcrWord


class GoogleVisionProvider(OCRProvider):
    name = "google_vision"

    def __init__(self, use_mock: Optional[bool] = None):
        self.client = None
        self.use_mock = use_mock if use_mock is not None else not bool(settings.GOOGLE_APPLICATION_CREDENTIALS)
        if not self.use_mock:
            self._init_client()

    def _init_client(self) -> None:
        try:
            from google.cloud import vision
            self.client = vision.ImageAnnotatorClient.from_service_account_json(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
        except Exception as e:
            self.use_mock = True

    def process_image(self, image: Image.Image, language: str = "en") -> OcrResult:
        if self.use_mock:
            return self._mock_process(image)
        return self._live_process(image, language)

    def _live_process(self, image: Image.Image, language: str = "en") -> OcrResult:
        from google.cloud import vision

        start = time.time()
        content = self._image_to_bytes(image)
        gcv_image = vision.Image(content=content)

        image_context = vision.ImageContext(language_hints=[language])
        response = self.client.text_detection(
            image=gcv_image,
            image_context=image_context,
            timeout=settings.OCR_GOOGLE_VISION_TIMEOUT,
        )

        elapsed = (time.time() - start) * 1000

        if response.error.message:
            raise RuntimeError(f"Google Vision API error: {response.error.message}")

        full_text = response.full_text_annotation.text if response.full_text_annotation else ""

        blocks: list[OcrBlock] = []
        if response.text_annotations:
            word_confs: list[float] = []
            for annotation in response.text_annotations[1:]:
                vertices = [(v.x, v.y) for v in annotation.bounding_poly.vertices]
                flat_box = [v for pair in vertices for v in pair]
                words = [
                    OcrWord(
                        text=annotation.description,
                        confidence=round(annotation.confidence, 4) if annotation.confidence else 0.0,
                        bounding_box=flat_box,
                    )
                ]
                if annotation.confidence:
                    word_confs.append(annotation.confidence)
                blocks.append(
                    OcrBlock(
                        text=annotation.description,
                        confidence=round(annotation.confidence, 4) if annotation.confidence else 0.0,
                        block_type="text",
                        words=words,
                    )
                )

            avg_conf = round(sum(word_confs) / max(len(word_confs), 1), 4) if word_confs else 0.0
        else:
            avg_conf = 0.0

        return OcrResult(
            full_text=full_text,
            confidence=avg_conf,
            provider=self.name,
            pages=[],
            blocks=blocks,
            language=language,
            processing_time_ms=round(elapsed, 2),
        )

    def _mock_process(self, image: Image.Image, language: str = "en") -> OcrResult:
        start = time.time()
        w, h = image.size

        diagnostics = []
        if hasattr(image, "mode"):
            diagnostics.append(f"mode={image.mode}")

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
        import hashlib
        content_hash = hashlib.md5(image_bytes).hexdigest()
        seed = int(content_hash[:8], 16) % 1000

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
