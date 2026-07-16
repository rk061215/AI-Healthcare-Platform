from typing import Optional

from app.ocr.base_ocr import BaseOCR
from app.ocr.config import OCRConfig
from app.ocr.exceptions import OCREngineNotFoundError


class OCRFactory:
    _engines: dict[str, type[BaseOCR]] = {}

    @classmethod
    def register(cls, name: str, engine_cls: type[BaseOCR]) -> None:
        cls._engines[name] = engine_cls

    @classmethod
    def create(cls, engine_name: Optional[str] = None, config: Optional[OCRConfig] = None, **kwargs) -> BaseOCR:
        if config is None:
            config = OCRConfig()

        name = (engine_name or config.engine).lower()
        engine_cls = cls._engines.get(name)

        if engine_cls is None:
            raise OCREngineNotFoundError(
                f"OCR engine '{name}' is not registered. "
                f"Available engines: {', '.join(cls._engines.keys())}"
            )

        return engine_cls(config, **kwargs)
