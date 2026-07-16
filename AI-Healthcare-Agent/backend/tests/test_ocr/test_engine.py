from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image

from app.ocr.engine import OcrEngine
from app.ocr.schemas import OcrJobResult


def _create_temp_image(suffix: str = ".png") -> Path:
    tmp = NamedTemporaryFile(delete=False, suffix=suffix)
    img = Image.new("RGB", (200, 150), color="white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "Patient Name: John Doe", fill="black")
    img.save(tmp, format="PNG" if suffix == ".png" else "JPEG")
    tmp.close()
    return Path(tmp.name)


def test_engine_process_image():
    engine = OcrEngine(use_mock=True)
    path = _create_temp_image(".png")
    try:
        result = engine.process_document(path, "png")
        assert result.status == "completed"
        assert result.confidence > 0
        assert result.text_length > 0
        assert len(result.full_text) > 0
        assert result.provider == "tesseract_mock"
    finally:
        path.unlink(missing_ok=True)


def test_engine_process_jpeg():
    engine = OcrEngine(use_mock=True)
    path = _create_temp_image(".jpeg")
    try:
        result = engine.process_document(path, "jpeg")
        assert result.status == "completed"
        assert result.processing_time_ms >= 0
    finally:
        path.unlink(missing_ok=True)


def test_engine_returns_extracted_data():
    engine = OcrEngine(use_mock=True)
    path = _create_temp_image(".png")
    try:
        result = engine.process_document(path, "png")
        assert result.extracted_data is not None
        assert len(result.extracted_data) > 0
    finally:
        path.unlink(missing_ok=True)


def test_engine_has_pages():
    engine = OcrEngine(use_mock=True)
    path = _create_temp_image(".png")
    try:
        result = engine.process_document(path, "png")
        assert result.pages_processed >= 1
    finally:
        path.unlink(missing_ok=True)


def test_engine_retry_on_failure():
    engine = OcrEngine(use_mock=True)
    result = engine.process_document(Path("nonexistent_file.pdf"), "pdf")
    assert result.status == "failed"
    assert result.error_message is not None


def test_engine_confidence_value():
    engine = OcrEngine(use_mock=True)
    path = _create_temp_image(".png")
    try:
        result = engine.process_document(path, "png")
        assert 0 <= result.confidence <= 1.0
    finally:
        path.unlink(missing_ok=True)
