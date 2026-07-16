import time
from typing import Optional

from PIL import Image

from app.ocr.providers.base import OCRProvider
from app.ocr.schemas import OcrBlock, OcrResult, OcrWord


class TesseractProvider(OCRProvider):
    name = "tesseract"

    def __init__(self, use_mock: Optional[bool] = None):
        self.use_mock = use_mock if use_mock is not None else not self._is_available()
        self._tesseract_checked = False
        self._tesseract_available = False

    @staticmethod
    def _is_available() -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def process_image(self, image: Image.Image, language: str = "en") -> OcrResult:
        if self.use_mock:
            return self._mock_process(image, language)

        import pytesseract

        start = time.time()

        pil_img = image.convert("RGB")

        ocr_data = pytesseract.image_to_data(pil_img, lang=language, output_type=pytesseract.Output.DICT)

        elapsed = (time.time() - start) * 1000

        full_text = pytesseract.image_to_string(pil_img, lang=language)

        words: list[OcrWord] = []
        blocks: list[OcrBlock] = []
        current_block_text: list[str] = []
        current_block_confs: list[float] = []
        block_num = -1

        for i in range(len(ocr_data["text"])):
            word_text = ocr_data["text"][i].strip()
            conf = int(ocr_data["conf"][i]) / 100.0 if ocr_data["conf"][i] != "-1" else 0.0
            bn = ocr_data["block_num"][i]
            left = ocr_data["left"][i]
            top = ocr_data["top"][i]
            w = ocr_data["width"][i]
            h = ocr_data["height"][i]

            if bn != block_num and current_block_text:
                block_conf = round(sum(current_block_confs) / max(len(current_block_confs), 1), 4) if current_block_confs else 0.0
                blocks.append(
                    OcrBlock(
                        text=" ".join(current_block_text),
                        confidence=block_conf,
                        block_type="text",
                        words=list(words),
                    )
                )
                current_block_text = []
                current_block_confs = []
                words = []
                block_num = bn

            if word_text:
                word = OcrWord(
                    text=word_text,
                    confidence=round(conf, 4),
                    bounding_box=[left, top, left + w, top + h] if w > 0 and h > 0 else None,
                )
                words.append(word)
                current_block_text.append(word_text)
                current_block_confs.append(conf)

        if current_block_text:
            block_conf = round(sum(current_block_confs) / max(len(current_block_confs), 1), 4) if current_block_confs else 0.0
            blocks.append(
                OcrBlock(
                    text=" ".join(current_block_text),
                    confidence=block_conf,
                    block_type="text",
                    words=list(words),
                )
            )

        all_confs = [w.confidence for w in words if w.confidence > 0]
        avg_conf = round(sum(all_confs) / max(len(all_confs), 1), 4) if all_confs else 0.0

        return OcrResult(
            full_text=full_text.strip(),
            confidence=avg_conf,
            provider=self.name,
            pages=[],
            blocks=blocks,
            language=language,
            processing_time_ms=round(elapsed, 2),
        )

    def _mock_process(self, image: Image.Image, language: str = "en") -> OcrResult:
        from app.ocr.providers.google_vision import GoogleVisionProvider

        gv = GoogleVisionProvider(use_mock=True)
        base = gv.process_image(image, language)
        base.provider = "tesseract_mock"
        base.confidence = round(base.confidence * 0.85, 4)
        return base
