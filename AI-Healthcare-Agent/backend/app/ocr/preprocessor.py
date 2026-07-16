import math
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image, ImageFilter

from app.core.config import settings


class ImagePreprocessor:
    @staticmethod
    def preprocess_image(image: Image.Image) -> tuple[Image.Image, dict]:
        steps: list[str] = []
        img = image.convert("RGB")

        if settings.OCR_PREPROCESS_DENOISE:
            img = ImagePreprocessor._denoise(img)
            steps.append("denoise")

        if settings.OCR_PREPROCESS_DESKEW:
            img = ImagePreprocessor._deskew(img)
            steps.append("deskew")

        if settings.OCR_PREPROCESS_BINARIZE:
            img = ImagePreprocessor._binarize(img)
            steps.append("binarize")

        return img, {"steps": steps, "original_size": image.size, "final_size": img.size}

    @staticmethod
    def _denoise(image: Image.Image) -> Image.Image:
        return image.filter(ImageFilter.MedianFilter(size=3))

    @staticmethod
    def _deskew(image: Image.Image) -> Image.Image:
        try:
            import numpy as np

            img_array = np.array(image.convert("L"))
            coords = np.column_stack(np.where(img_array < 128))
            if coords.shape[0] < 10:
                return image

            from numpy.polynomial import polynomial as P

            y_vals = coords[:, 0].astype(float)
            x_vals = coords[:, 1].astype(float)

            if len(y_vals) > 10000:
                idx = np.random.choice(len(y_vals), 10000, replace=False)
                y_vals = y_vals[idx]
                x_vals = x_vals[idx]

            x_fit = P.polyfit(y_vals, x_vals, 1)
            angle = math.degrees(math.atan(x_fit[1]))

            if abs(angle) < 0.5:
                return image

            return image.rotate(angle, resample=Image.BICUBIC, expand=True)
        except ImportError:
            return image

    @staticmethod
    def _binarize(image: Image.Image) -> Image.Image:
        gray = image.convert("L")
        threshold = ImagePreprocessor._otsu_threshold(gray)
        return gray.point(lambda p: 255 if p > threshold else 0).convert("RGB")

    @staticmethod
    def _otsu_threshold(image: Image.Image) -> int:
        try:
            import numpy as np

            pixels = np.array(image, dtype=np.uint8)
            hist = np.zeros(256, dtype=np.float64)
            for i in range(256):
                hist[i] = np.sum(pixels == i)

            total = pixels.size
            if total == 0:
                return 128

            hist = hist / total
            best_threshold = 128
            best_var = 0.0

            for t in range(1, 255):
                w0 = np.sum(hist[:t])
                w1 = np.sum(hist[t:])
                if w0 == 0 or w1 == 0:
                    continue
                mu0 = np.sum(np.arange(t) * hist[:t]) / w0
                mu1 = np.sum(np.arange(t, 256) * hist[t:]) / w1
                var = w0 * w1 * (mu0 - mu1) ** 2
                if var > best_var:
                    best_var = var
                    best_threshold = t

            return best_threshold
        except ImportError:
            return 128

    @staticmethod
    def split_pages(image: Image.Image) -> list[Image.Image]:
        w, h = image.size
        if h <= w * 1.3:
            return [image]

        mid = h // 2
        top = image.crop((0, 0, w, mid))
        bottom = image.crop((0, mid, w, h))
        return [top, bottom]

    @staticmethod
    def pdf_to_images(pdf_path: Path, dpi: Optional[int] = None) -> list[Image.Image]:
        dpi = dpi or settings.OCR_IMAGE_DPI
        try:
            import pdf2image
            return pdf2image.convert_from_path(str(pdf_path), dpi=dpi)
        except ImportError:
            pass

        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            images: list[Image.Image] = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
            return images
        except ImportError:
            pass

        try:
            import subprocess
            out_dir = Path(tempfile.mkdtemp())
            result = subprocess.run(
                ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(out_dir / "page")],
                capture_output=True, timeout=120,
            )
            if result.returncode == 0:
                pages = sorted(out_dir.glob("*.png"))
                return [Image.open(p) for p in pages]
        except Exception:
            pass

        raise RuntimeError(
            "No PDF-to-image backend available. Install pdf2image (with poppler) or PyMuPDF."
        )
