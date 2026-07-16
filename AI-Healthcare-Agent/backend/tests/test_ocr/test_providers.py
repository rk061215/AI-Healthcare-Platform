from io import BytesIO

from PIL import Image

from app.ocr.engines.future.google_vision import GoogleVisionEngine
from app.ocr.engines.tesseract_ocr import TesseractEngine


def _create_test_image() -> Image.Image:
    img = Image.new("RGB", (200, 150), color="white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "Hello World", fill="black")
    return img


def test_google_vision_mock_returns_result():
    engine = GoogleVisionEngine()
    img = _create_test_image()
    result = engine._mock_process(img)
    assert result.provider == "google_vision_mock"
    assert result.confidence > 0
    assert len(result.full_text) > 0
    assert result.processing_time_ms >= 0


def test_google_vision_mock_contains_expected_text():
    engine = GoogleVisionEngine()
    img = _create_test_image()
    result = engine._mock_process(img)
    assert "Patient" in result.full_text or "Name" in result.full_text


def test_google_vision_mock_has_blocks():
    engine = GoogleVisionEngine()
    img = _create_test_image()
    result = engine._mock_process(img)
    assert len(result.blocks) > 0
    assert result.blocks[0].confidence > 0


def test_google_vision_mock_has_words():
    engine = GoogleVisionEngine()
    img = _create_test_image()
    result = engine._mock_process(img)
    all_words = [w for block in result.blocks for w in block.words]
    assert len(all_words) > 0
    for w in all_words:
        assert w.confidence > 0


def test_google_vision_mock_different_images():
    engine = GoogleVisionEngine()

    img1 = Image.new("RGB", (100, 100), color="white")
    result1 = engine._mock_process(img1)

    img2 = Image.new("RGB", (400, 300), color="black")
    result2 = engine._mock_process(img2)

    assert result1.full_text != result2.full_text or result1.confidence != result2.confidence


def test_tesseract_mock_returns_result():
    engine = TesseractEngine(use_mock=True)
    img = _create_test_image()
    result = engine.process_image(img)
    assert "tesseract" in result.provider
    assert result.confidence > 0
    assert len(result.full_text) > 0


def test_tesseract_mock_lower_confidence():
    gv = GoogleVisionEngine()
    ts = TesseractEngine(use_mock=True)
    img = _create_test_image()
    gv_result = gv._mock_process(img)
    ts_result = ts.process_image(img)
    assert ts_result.confidence < gv_result.confidence
