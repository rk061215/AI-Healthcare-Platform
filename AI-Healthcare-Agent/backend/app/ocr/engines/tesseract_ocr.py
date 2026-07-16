import hashlib
import time
from typing import Optional

from PIL import Image

from app.ocr.base_ocr import BaseOCR
from app.ocr.config import OCRConfig
from app.ocr.exceptions import OCRLanguageNotSupportedError, OCRProcessingError
from app.ocr.ocr_factory import OCRFactory
from app.ocr.schemas import OcrBlock, OcrResult, OcrWord


class TesseractEngine(BaseOCR):
    name = "tesseract"

    def __init__(self, config: Optional[OCRConfig] = None, use_mock: Optional[bool] = None):
        self.config = config or OCRConfig()
        self._available = False
        self._tesseract_checked = False
        self.use_mock = use_mock if use_mock is not None else False

    def _check_available(self) -> None:
        if self._tesseract_checked:
            return
        self._tesseract_checked = True
        try:
            import pytesseract
            if self.config.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
            pytesseract.get_tesseract_version()
            self._available = True
        except Exception:
            self._available = False

    def _ensure_available(self) -> None:
        if self.use_mock:
            return
        self._check_available()
        if not self._available:
            raise OCRProcessingError(
                "Tesseract OCR is not installed or not found in PATH. "
                "Install Tesseract manually or set TESSERACT_CMD in config."
            )

    def _validate_language(self, language: str) -> str:
        lang_map = {
            "en": "eng",
            "es": "spa",
            "fr": "fra",
            "de": "deu",
            "it": "ita",
            "pt": "por",
            "hi": "hin",
            "ar": "ara",
            "zh": "chi_sim",
            "ja": "jpn",
            "ko": "kor",
        }
        mapped = lang_map.get(language, language)
        try:
            import pytesseract
            supported = pytesseract.get_languages()
            if mapped not in supported:
                available = ", ".join(supported[:10])
                raise OCRLanguageNotSupportedError(
                    f"Language '{language}' (mapped: '{mapped}') is not installed. "
                    f"Available: {available}. "
                    f"Install with: apt-get install tesseract-ocr-{mapped.replace('_', '-')}"
                )
        except OCRLanguageNotSupportedError:
            raise
        except Exception:
            pass
        return mapped

    def process_image(self, image: Image.Image, language: str = "en") -> OcrResult:
        if self.use_mock:
            return self._mock_process(image, language)

        self._ensure_available()
        import pytesseract

        mapped_lang = self._validate_language(language)
        start = time.time()

        pil_img = image.convert("RGB")

        ocr_data = pytesseract.image_to_data(pil_img, lang=mapped_lang, output_type=pytesseract.Output.DICT)
        elapsed = (time.time() - start) * 1000
        full_text = pytesseract.image_to_string(pil_img, lang=mapped_lang)

        words: list[OcrWord] = []
        blocks: list[OcrBlock] = []
        current_block_text: list[str] = []
        current_block_confs: list[float] = []
        block_num = -1

        for i in range(len(ocr_data["text"])):
            word_text = ocr_data["text"][i].strip()
            if not word_text:
                continue
            conf = int(ocr_data["conf"][i]) / 100.0
            word_block = ocr_data["block_num"][i]

            if word_block != block_num and current_block_text:
                block_conf = sum(current_block_confs) / max(len(current_block_confs), 1)
                blocks.append(
                    OcrBlock(
                        text=" ".join(current_block_text),
                        confidence=round(block_conf, 4),
                        words=list(words[-len(current_block_text):]) if words else [],
                    )
                )
                current_block_text = []
                current_block_confs = []
                block_num = word_block

            block_num = word_block
            current_block_text.append(word_text)
            current_block_confs.append(conf)

            words.append(
                OcrWord(
                    text=word_text,
                    confidence=round(conf, 4),
                    x=ocr_data["left"][i],
                    y=ocr_data["top"][i],
                    width=ocr_data["width"][i],
                    height=ocr_data["height"][i],
                )
            )

        if current_block_text:
            block_conf = sum(current_block_confs) / max(len(current_block_confs), 1)
            blocks.append(
                OcrBlock(
                    text=" ".join(current_block_text),
                    confidence=round(block_conf, 4),
                    words=list(words[-len(current_block_text):]),
                )
            )

        word_confs = [w.confidence for w in words if w.confidence > 0]
        avg_conf = sum(word_confs) / max(len(word_confs), 1) if word_confs else 0.0

        return OcrResult(
            full_text=full_text.strip(),
            confidence=round(avg_conf, 4),
            provider=self.name,
            pages=[],
            blocks=blocks,
            words=words,
            language=language,
            processing_time_ms=round(elapsed, 2),
            has_more_pages=False,
        )

    def _mock_process(self, image: Image.Image, language: str = "en") -> OcrResult:
        from app.ocr.engines.future.google_vision import GoogleVisionEngine

        gv = GoogleVisionEngine(self.config)
        base = gv._mock_process(image, language)
        base.provider = "tesseract_mock"
        base.confidence = round(base.confidence * 0.85, 4)
        return base


OCRFactory.register("tesseract", TesseractEngine)
