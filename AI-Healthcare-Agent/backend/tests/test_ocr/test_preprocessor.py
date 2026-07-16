from io import BytesIO

from PIL import Image, ImageChops

from app.ocr.preprocessor import ImagePreprocessor


def _create_test_image(width: int = 200, height: int = 300) -> Image.Image:
    img = Image.new("RGB", (width, height), color="white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((20, 50), "Patient Name: John Doe", fill="black")
    draw.text((20, 80), "Date: 2024-01-15", fill="black")
    draw.text((20, 110), "Diagnosis: Hypertension", fill="black")
    return img


def test_denoise():
    img = _create_test_image()
    processed, info = ImagePreprocessor.preprocess_image(img)
    assert processed is not None
    assert "denoise" in info["steps"]
    assert info["original_size"] == (200, 300)


def test_deskew_no_skew():
    img = _create_test_image()
    processed, info = ImagePreprocessor.preprocess_image(img)
    assert "denoise" in info["steps"]


def test_binarize():
    img = _create_test_image()
    processed, info = ImagePreprocessor.preprocess_image(img)
    assert processed.mode == "RGB"


def test_otsu_threshold():
    img = _create_test_image()
    gray = img.convert("L")
    threshold = ImagePreprocessor._otsu_threshold(gray)
    assert 0 <= threshold <= 255


def test_preprocess_all_steps():
    img = _create_test_image(300, 400)
    processed, info = ImagePreprocessor.preprocess_image(img)
    assert info["steps"] == ["denoise", "deskew", "binarize"]
    assert info["final_size"] is not None


def test_split_pages_tall_image():
    img = _create_test_image(200, 600)
    pages = ImagePreprocessor.split_pages(img)
    assert len(pages) == 2
    assert pages[0].size == (200, 300)
    assert pages[1].size == (200, 300)


def test_split_pages_short_image():
    img = _create_test_image(400, 300)
    pages = ImagePreprocessor.split_pages(img)
    assert len(pages) == 1


def test_preprocessor_disabled():
    import app.core.config as config
    original_denoise = config.settings.OCR_PREPROCESS_DENOISE
    original_deskew = config.settings.OCR_PREPROCESS_DESKEW
    original_binarize = config.settings.OCR_PREPROCESS_BINARIZE
    config.settings.OCR_PREPROCESS_DENOISE = False
    config.settings.OCR_PREPROCESS_DESKEW = False
    config.settings.OCR_PREPROCESS_BINARIZE = False
    img = _create_test_image()
    processed, info = ImagePreprocessor.preprocess_image(img)
    assert info["steps"] == []
    config.settings.OCR_PREPROCESS_DENOISE = original_denoise
    config.settings.OCR_PREPROCESS_DESKEW = original_deskew
    config.settings.OCR_PREPROCESS_BINARIZE = original_binarize


def test_pdf_to_images_missing_backend(monkeypatch):
    monkeypatch.setattr("app.ocr.preprocessor.ImagePreprocessor.pdf_to_images", lambda p, dpi=300: [])
    from pathlib import Path
    result = ImagePreprocessor.pdf_to_images(Path("nonexistent.pdf"))
    assert result == []
