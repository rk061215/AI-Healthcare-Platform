from pathlib import Path

from app.core.config import settings


class GoogleVisionOCR:
    def __init__(self):
        self.client = None
        self.credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS

    async def initialize(self) -> None:
        raise NotImplementedError("Google Vision OCR will be initialized in the next phase")

    async def extract_text(self, image_path: Path) -> str:
        raise NotImplementedError("OCR extraction will be implemented in the next phase")

    async def extract_text_from_pdf(self, pdf_path: Path) -> str:
        raise NotImplementedError("PDF OCR will be implemented in the next phase")
