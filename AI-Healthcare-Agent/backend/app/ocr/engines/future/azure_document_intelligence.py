from typing import Optional

from PIL import Image

from app.ocr.base_ocr import BaseOCR
from app.ocr.config import OCRConfig
from app.ocr.ocr_factory import OCRFactory
from app.ocr.schemas import OcrResult


class AzureDocumentIntelligenceEngine(BaseOCR):
    name = "azure_document_intelligence"

    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()

    def process_image(self, image: Image.Image, language: str = "en") -> OcrResult:
        raise NotImplementedError(
            "Azure Document Intelligence OCR engine is not yet implemented. "
            "Implement process_image() to enable Azure Document Intelligence support."
        )


OCRFactory.register("azure_document_intelligence", AzureDocumentIntelligenceEngine)
