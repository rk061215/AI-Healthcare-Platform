# Document Processing Pipeline

> Complete architecture for the document processing pipeline, from upload to
> searchable vector embeddings. This document governs ALL implementation of
> document processing features.
>
> **Status:** Design Phase (pre-implementation)
> **Last Updated:** 2026-07-14
> **Author:** AI Healthcare Team
> **Applies To:** Reports, Prescriptions, Lab Results, Discharge Summaries

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Upload](#2-upload)
3. [Validation](#3-validation)
4. [Virus Scan](#4-virus-scan)
5. [Storage](#5-storage)
6. [OCR](#6-ocr)
7. [Preprocessing](#7-preprocessing)
8. [Chunking](#8-chunking)
9. [Medical Entity Extraction](#9-medical-entity-extraction)
10. [Medicine Parsing](#10-medicine-parsing)
11. [JSON Validation](#11-json-validation)
12. [Database Storage](#12-database-storage)
13. [Embedding Creation](#13-embedding-creation)
14. [Vector Database](#14-vector-database)
15. [RAG](#15-rag)
16. [Failure Recovery](#16-failure-recovery)
17. [Background Processing](#17-background-processing)
18. [Retry Logic](#18-retry-logic)
19. [Queue Architecture](#19-queue-architecture)
20. [Architecture Decision Records](#20-architecture-decision-records)

---

## 1. Pipeline Overview

### 1.1 End-to-End Flow

```
                         ┌──────────────────────┐
                         │    Client Uploads     │
                         │    (POST /upload)     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       STAGE 1: INGEST          │
                    │  ┌─────────┐  ┌──────────┐    │
                    │  │ Validate │──► Virus    │    │
                    │  │ File     │  │ Scan     │    │
                    │  └─────────┘  └─────┬────┘    │
                    │                     ▼         │
                    │  ┌────────────────────────┐   │
                    │  │  Storage (Disk + DB)    │   │
                    │  │  Report.status=uploaded │   │
                    │  └───────────┬────────────┘   │
                    └──────────────┼────────────────┘
                                   │  (enqueue to pipeline)
                                   ▼
                    ┌───────────────────────────────┐
                    │       STAGE 2: OCR             │
                    │  ┌──────────┐  ┌──────────┐   │
                    │  │ Pre-     │──► OCR      │   │
                    │  │ process  │  │ (Google   │   │
                    │  │ images   │  │ Vision)   │   │
                    │  └──────────┘  └─────┬────┘   │
                    │                     ▼         │
                    │  ┌────────────────────────┐   │
                    │  │  Reconstruct text       │   │
                    │  │  (multi-page assembly)  │   │
                    │  │  Report.status=ocr_done │   │
                    │  └───────────┬────────────┘   │
                    └──────────────┼────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │    STAGE 3: EXTRACTION         │
                    │  ┌──────────┐  ┌──────────┐   │
                    │  │ Medical  │──► Medicine │   │
                    │  │ Entity   │  │ Parsing   │   │
                    │  │ Extract  │  └─────┬────┘   │
                    │  └──────────┘        │         │
                    │                      ▼         │
                    │  ┌──────────┐  ┌──────────┐   │
                    │  │ JSON     │──► DB       │   │
                    │  │ Validate │  │ Store    │   │
                    │  └──────────┘  └─────┬────┘   │
                    │                      │         │
                    │  Report.status=      │         │
                    │  completed/failed    │         │
                    └──────────────────────┼─────────┘
                                           │
                                           ▼
                    ┌───────────────────────────────┐
                    │    STAGE 4: INDEXING           │
                    │  ┌──────────┐  ┌──────────┐   │
                    │  │ Chunk    │──► Embed    │   │
                    │  │ Text     │  │          │   │
                    │  └──────────┘  └─────┬────┘   │
                    │                      ▼         │
                    │  ┌────────────────────────┐   │
                    │  │  Store in ChromaDB      │   │
                    │  │  (vector + metadata)    │   │
                    │  └────────────────────────┘   │
                    └───────────────────────────────┘
```

### 1.2 Pipeline Stages Summary

| Stage | Name | Input | Output | Status Field |
|-------|------|-------|--------|-------------|
| 1 | **Ingest** | Uploaded file | File on disk, DB record | `uploaded` |
| 2 | **OCR** | Image/PDF files | Raw text | `ocr_done` |
| 3 | **Extract** | Raw text | Structured JSON (medicines, disease) | `completed` / `failed` |
| 4 | **Index** | Raw text + metadata | Vector embeddings in ChromaDB | (async, no status change) |

### 1.3 Status State Machine

```
                    ┌──────────┐
                    │  pending │  (initial state on upload)
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
              ┌────►│ uploaded │  (file written to disk)
              │     └────┬─────┘
              │          │
              │          ▼
              │     ┌──────────┐
              │     │processing│  (picked up by queue worker)
              │     └────┬─────┘
              │          │
              │    ┌─────┴──────┐
              │    │            │
              │    ▼            ▼
              │ ┌────────┐ ┌────────┐
              │ │ocr_done│ │ failed │
              │ └────┬───┘ └────────┘
              │      │         ▲
              │      ▼         │
              │ ┌──────────┐   │
              │ │completed │   │
              │ └────┬─────┘   │
              │      │         │
              │      ▼         │
              │ ┌──────────┐   │
              │ │ indexed  │   │
              │ └──────────┘   │
              │                │
              └────────────────┘ (re-processing = pending → processing)

  Valid transitions:
    pending  → uploaded
    uploaded → processing
    processing → ocr_done | failed
    ocr_done → completed | failed
    completed → indexed | failed
    any      → failed (on unrecoverable error)
    failed   → processing (manual retry)
```

### 1.4 Data Flow Between Stages

```
STAGE 1 output (Report record):
  { id, patient_id, file_path, file_type, file_size, status: "uploaded" }

STAGE 2 output (OCR result):
  { report_id, raw_text: str, pages: [{page_num, text, confidence}] }

STAGE 3 output (Extraction result):
  { report_id, disease, medicines: [...], follow_up_date, doctor_instructions,
    confidence, validation_status }

STAGE 4 output (Indexing result):
  { report_id, chunk_count, embedding_count, vector_ids: [...] }
```

---

## 2. Upload

### 2.1 Upload Endpoint

```python
# POST /api/v1/reports/upload
# Content-Type: multipart/form-data
# Body: file (UploadFile), title (optional string)
```

### 2.2 Handler Logic

```
receive_upload(file, patient_id, title)
    │
    ├── 1. Authenticate patient (JWT)
    ├── 2. Generate unique file_id (UUID v4)
    ├── 3. Determine extension from original filename
    ├── 4. Write to disk: {upload_dir}/{patient_id}/{file_id}{ext}
    ├── 5. Create Report DB record: status="pending"
    ├── 6. Return { report_id, status, filename }
    └── 7. Enqueue to pipeline (async): { report_id, file_path }
```

### 2.3 Upload Response

```json
{
  "id": "uuid-of-report",
  "title": "prescription.pdf",
  "status": "pending",
  "file_type": "pdf",
  "file_size": 245760,
  "uploaded_at": "2026-07-14T10:30:00Z",
  "estimated_completion_seconds": 45
}
```

### 2.4 Concurrent Upload Limits

| Limit | Value | Rationale |
|-------|-------|-----------|
| Max files per request | 1 | Simplicity; batch upload is future scope |
| Max concurrent uploads per patient | 5 | Prevents abuse; returns 429 |
| Max total upload size per patient/day | 100 MB | Storage quota |
| Upload timeout | 30 seconds | For large files; nginx/gunicorn aligned |

### 2.5 Upload Quarantine

Uploaded files are initially written to a **quarantine directory** that is NOT
served by static file handlers:

```
{upload_dir}/{patient_id}/quarantine/{file_id}{ext}
```

Files are moved to the permanent directory ONLY after virus scan passes.

---

## 3. Validation

### 3.1 File Validation Layers

```
                    ┌──────────────────────────────────────┐
                    │         Layer 1: HTTP Validation      │
                    │  • Content-Type header check          │
                    │  • File size check (content-length)   │
                    │  • Multipart form parsing             │
                    └──────────────────────────────────────┘
                                      │
                    ┌──────────────────────────────────────┐
                    │         Layer 2: Extension Check      │
                    │  • Allowed: .pdf, .jpg, .jpeg, .png  │
                    │  • Rejected: .exe, .zip, .html, etc  │
                    │  • Extension must match magic bytes   │
                    └──────────────────────────────────────┘
                                      │
                    ┌──────────────────────────────────────┐
                    │         Layer 3: Magic Byte Check     │
                    │  • Read first 512 bytes               │
                    │  • Verify against known signatures:   │
                    │    • PDF:  %PDF                        │
                    │    • JPEG: \xFF\xD8\xFF               │
                    │    • PNG:  \x89PNG                    │
                    └──────────────────────────────────────┘
                                      │
                    ┌──────────────────────────────────────┐
                    │         Layer 4: Application Check    │
                    │  • PDF: parseable? page count > 0     │
                    │  • Image: dimensions > 0, not corrupt │
                    │  • DICOM: valid header, patient match │
                    └──────────────────────────────────────┘
```

### 3.2 Validation Rules

| Rule | Implementation | Error Response |
|------|---------------|----------------|
| File extension allowed | Check against `ALLOWED_EXTENSIONS` config | 400: "File type .xyz not allowed" |
| File size ≤ 10 MB | Check `content-length` and actual bytes read | 400: "File exceeds 10MB limit" |
| Extension matches content | Compare extension with `python-magic` MIME type | 400: "File extension does not match content" |
| PDF parseable | Attempt `pypdf.PdfReader` — catch all exceptions | 422: "PDF file is corrupted or empty" |
| Image valid | `PIL.Image.open()` + `verify()` | 422: "Image file is corrupted" |
| DICOM valid | Check for `DICM` prefix at byte 128 | 422: "Invalid DICOM file" |
| No embedded scripts | Scan for JavaScript in PDF, EXIF in images | 422: "File contains embedded content" |

### 3.3 Magic Byte Signatures

```python
MAGIC_BYTES = {
    "pdf":  { b"\x25\x50\x44\x46": ".pdf" },
    "jpeg": { b"\xff\xd8\xff": ".jpg" },
    "png":  { b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": ".png" },
}
```

### 3.4 Quarantine Logic

```python
async def validate_and_quarantine(file: UploadFile, patient_id: str) -> ValidationResult:
    """Validate file and move to quarantine if checks pass."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)

    # 1. Size check
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return ValidationResult(valid=False, error="File too large")

    # 2. Magic byte check
    magic = content[:8]
    detected_type = None
    for ext, signatures in MAGIC_BYTES.items():
        for signature, expected_ext in signatures.items():
            if magic.startswith(signature):
                detected_type = ext
                break
    if not detected_type:
        return ValidationResult(valid=False, error="Unrecognized file type")

    # 3. Extension matches content
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext != detected_type:
        return ValidationResult(valid=False, error=f"Extension .{ext} doesn't match content type {detected_type}")

    # 4. Application-level check
    app_valid = await validate_content(tmp.name, detected_type)
    if not app_valid:
        return ValidationResult(valid=False, error=f"Corrupted or invalid {detected_type} file")

    # 5. Move to quarantine
    quarantine_path = settings.upload_path / patient_id / "quarantine"
    quarantine_path.mkdir(parents=True, exist_ok=True)
    shutil.move(tmp.name, quarantine_path / f"{file_id}.{detected_type}")

    return ValidationResult(
        valid=True,
        file_path=str(quarantine_path / f"{file_id}.{detected_type}"),
        file_type=detected_type,
        file_size=len(content),
    )
```

---

## 4. Virus Scan

### 4.1 Scan Strategy

| Aspect | Decision |
|--------|----------|
| **Scanner** | ClamAV (`clamd` client over TCP socket) |
| **When** | After file validation, before moving to permanent storage |
| **Timeout** | 30 seconds per file |
| **Action on threat** | Delete quarantined file, set status = "failed", log security event |
| **Action on scan error** | Log warning, proceed (fail-open) |
| **Infrastructure** | Docker container `clamav` sidecar |

### 4.2 Scan Flow

```python
async def virus_scan(file_path: Path) -> ScanResult:
    """Scan file with ClamAV. Returns clean/infected/error."""
    try:
        async with aiofiles.open(file_path, "rb") as f:
            file_data = await f.read()
        response = await clamd_client.instream(file_data)
        status = response.get("Stream", ("ERROR",))[0]
        if status == "FOUND":
            logger.warning(f"Virus detected in {file_path}: {response}")
            return ScanResult(clean=False, threat=response.get("Stream", ("", ""))[1])
        return ScanResult(clean=True)
    except ConnectionRefusedError:
        logger.error("ClamAV not available — skipping virus scan")
        return ScanResult(clean=True, skipped=True)
    except Exception as e:
        logger.error(f"Virus scan failed for {file_path}: {e}")
        return ScanResult(clean=True, skipped=True)
```

### 4.3 Threat Response

| Scenario | Response |
|----------|----------|
| Clean file | Move to permanent storage immediately |
| Infected file | Delete from quarantine, set report status = "failed", error_message = "Virus detected", log security alert |
| Scan unavailable | Proceed but log warning; periodic security audit cleans unscanned files |
| Scan timeout | Proceed but flag for manual review |

### 4.4 Security Logging

```sql
CREATE TABLE security_scan_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path VARCHAR(500) NOT NULL,
    patient_id UUID,
    scan_status VARCHAR(20) NOT NULL,        -- "clean", "infected", "skipped", "error"
    threat_name VARCHAR(255),
    scanner_version VARCHAR(100),
    scan_duration_ms INTEGER,
    action_taken VARCHAR(50),                 -- "moved", "deleted", "quarantined", "proceeded"
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Storage

### 5.1 Directory Structure

```
{settings.UPLOAD_DIR}/
├── {patient_uuid}/
│   ├── quarantine/
│   │   └── {file_id}.pdf          # Temporary: deleted after virus scan passes
│   ├── originals/
│   │   └── {file_id}.pdf          # Permanent: original uploaded file
│   ├── processed/
│   │   ├── {file_id}_page_1.png   # Per-page PNGs for OCR
│   │   ├── {file_id}_page_2.png
│   │   └── {file_id}.txt          # Extracted OCR text
│   └── thumbnails/
│       └── {file_id}_thumb.jpg    # Preview thumbnail (100x100)
├── temp/                          # Cleaned every 24 hours
└── quarantine/                     # Unscanned files (cleaned by security audit)
```

### 5.2 File Naming Convention

```
{file_id}.{ext}              — Original uploaded file
{file_id}_page_{n}.png       — Per-page images (after PDF conversion)
{file_id}.txt                — Aggregated OCR text
{file_id}_thumb.jpg          — Thumbnail preview
{file_id}_metadata.json      — Processing metadata (optional, for debugging)
```

### 5.3 Storage Backend

| Environment | Backend | Config |
|-------------|---------|--------|
| Development | Local disk | `UPLOAD_DIR=./uploads` |
| Production | S3-compatible (MinIO) | `S3_BUCKET`, `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` |

### 5.4 S3 Abstraction

```python
class FileStorage(ABC):
    """Abstract file storage backend — supports local disk and S3."""

    @abstractmethod
    async def store(self, path: str, content: bytes) -> str:
        """Store a file. Returns the full path/key."""

    @abstractmethod
    async def retrieve(self, path: str) -> bytes:
        """Retrieve a file by path/key."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete a file by path/key."""

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if a file exists."""


class LocalFileStorage(FileStorage):
    """Local disk implementation for development/testing."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    async def store(self, path: str, content: bytes) -> str:
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return str(full_path)


class S3FileStorage(FileStorage):
    """S3-compatible implementation for production."""

    def __init__(self, bucket: str, endpoint: str, access_key: str, secret_key: str):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
```

### 5.5 Storage Security Rules

- Files are stored in patient-scoped directories — never accessible by other patients
- The API serves files through authenticated endpoints, not directly from disk
- Static file serving is disabled for the uploads directory
- File paths stored in DB use forward slashes regardless of OS
- Original files are **never** modified after upload — all processing creates derivative files

---

## 6. OCR

### 6.1 OCR Provider Strategy

| Provider | Use Case | When | Model |
|----------|----------|------|-------|
| **Google Cloud Vision** | Primary OCR | All image/PDF uploads | `document_text_detection` |
| **Tesseract** | Fallback | When Google Vision is unavailable | `eng` + `osd` |
| **pypdf** | Native PDF text | PDFs with embedded text layer | Direct text extraction |

### 6.2 OCR Selection Logic

```python
async def select_ocr_method(file_path: Path, file_type: str) -> str:
    """Select the best OCR method for the given file."""
    if file_type == "pdf":
        # Check if PDF has embedded text
        text = await extract_pdf_text_direct(file_path)
        if text.strip():
            return "direct_pdf"       # Fast path — no OCR needed
        return "google_vision"         # Scanned PDF — needs OCR

    if file_type in ("jpg", "jpeg", "png"):
        return "google_vision"         # Image — always OCR

    if file_type == "dicom":
        return "google_vision"         # Medical image — OCR

    return "tesseract"                 # Fallback
```

### 6.3 Google Cloud Vision Integration

```python
class GoogleVisionOCR:
    """OCR client for Google Cloud Vision API."""

    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
        self.max_retries = 3
        self.timeout = 30  # seconds

    async def extract_text(self, image_path: Path) -> OCRResult:
        """Extract text from a single image."""
        with open(image_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)

        response = await self.client.document_text_detection(
            image=image,
            image_context=vision.ImageContext(
                language_hints=["en"],
            ),
            timeout=self.timeout,
        )

        if response.error.message:
            raise OCRError(f"Google Vision API error: {response.error.message}")

        # Extract full text
        full_text = response.full_text_annotation.text

        # Extract per-page/block structure
        pages = []
        for page in response.full_text_annotation.pages:
            page_text = ""
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        page_text += "".join([symbol.text for symbol in word.symbols]) + " "
                    page_text += "\n"
            pages.append({
                "page_num": len(pages) + 1,
                "text": page_text.strip(),
                "confidence": page.confidence,
            })

        return OCRResult(
            raw_text=full_text,
            pages=pages,
            confidence=response.full_text_annotation.pages[0].confidence if response.full_text_annotation.pages else 0,
            method="google_vision",
        )

    async def extract_text_from_pdf(self, pdf_path: Path) -> OCRResult:
        """Convert PDF to images, OCR each page, merge results."""
        images = await pdf_to_images(pdf_path, dpi=300)
        all_text = []
        all_pages = []
        for i, img in enumerate(images):
            page_path = pdf_path.parent / f"{pdf_path.stem}_page_{i+1}.png"
            img.save(page_path, "PNG")
            result = await self.extract_text(page_path)
            all_text.append(result.raw_text)
            all_pages.extend(result.pages)
            page_path.unlink()  # Clean up temp page image

        return OCRResult(
            raw_text="\n\n".join(all_text),
            pages=all_pages,
            confidence=sum(p["confidence"] for p in all_pages) / len(all_pages) if all_pages else 0,
            method="google_vision",
        )
```

### 6.4 OCR Result Schema

```python
@dataclass
class OCRResult:
    raw_text: str                           # Complete extracted text
    pages: list[PageResult]                 # Per-page breakdown
    confidence: float                       # 0.0 - 1.0
    method: str                             # "google_vision" | "tesseract" | "direct_pdf"
    processing_time_ms: int                 # Total OCR time
    word_count: int                         # Number of words detected
    language: str                           # Detected language code

@dataclass
class PageResult:
    page_num: int
    text: str
    confidence: float
    block_count: int
    paragraphs: list[dict]                  # [{text, confidence, bounding_box}]
```

### 6.5 Tesseract Fallback

```python
class TesseractOCR:
    """Fallback OCR when Google Vision is unavailable."""

    def __init__(self):
        self.tesseract_cmd = "tesseract"

    async def extract_text(self, image_path: Path) -> OCRResult:
        """Extract text using Tesseract OCR."""
        import pytesseract

        img = Image.open(image_path)
        # Preprocess for better Tesseract results
        img = img.convert("L")              # Grayscale
        img = img.point(lambda x: 0 if x < 128 else 255)  # Threshold

        text = pytesseract.image_to_string(img, lang="eng")
        data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)

        confidences = [int(c) for c in data["conf"] if c != "-1"]
        avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0

        return OCRResult(
            raw_text=text,
            pages=[PageResult(page_num=1, text=text, confidence=avg_confidence, block_count=0, paragraphs=[])],
            confidence=avg_confidence,
            method="tesseract",
            processing_time_ms=0,
            word_count=len(text.split()),
            language="en",
        )
```

### 6.6 Direct PDF Text Extraction

```python
class DirectPDFExtractor:
    """Extract text directly from PDFs with embedded text layers."""

    async def extract(self, pdf_path: Path) -> OCRResult:
        """Extract text from a PDF with native text content."""
        import pypdf

        reader = pypdf.PdfReader(pdf_path)
        pages = []
        full_text = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages.append(PageResult(
                page_num=i + 1,
                text=text,
                confidence=1.0,            # Direct extraction — no confidence measure
                block_count=len(page.images) + 1,
                paragraphs=[{"text": text, "confidence": 1.0, "bounding_box": None}],
            ))
            full_text.append(text)

        return OCRResult(
            raw_text="\n\n".join(full_text),
            pages=pages,
            confidence=1.0,
            method="direct_pdf",
            processing_time_ms=0,
            word_count=len(" ".join(full_text).split()),
            language="en",
        )
```

### 6.7 OCR Quality Thresholds

| OCR Confidence | Action |
|---------------|--------|
| ≥ 0.9 | Proceed with extraction |
| 0.7 – 0.9 | Proceed with extraction, flag for review |
| 0.5 – 0.7 | Proceed with extraction, require human verification |
| < 0.5 | Mark as failed, request re-upload of clearer copy |

---

## 7. Preprocessing

### 7.1 Image Preprocessing Pipeline

```
                    ┌──────────────────────┐
                    │    Raw Image/PDF      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 1: Orientation   │
                    │ Correct rotation      │
                    │ using EXIF data +     │
                    │ Tesseract OSD         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 2: Grayscale     │
                    │ Convert to single     │
                    │ channel (L mode)      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 3: Denoise       │
                    │ Median filter         │
                    │ (kernel size 3)       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 4: Contrast      │
                    │ CLAHE (Contrast       │
                    │ Limited Adaptive      │
                    │ Histogram Equaliz.)   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 5: Binarize      │
                    │ Adaptive threshold    │
                    │ or Otsu's method      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 6: Deskew        │
                    │ Detect + correct      │
                    │ text skew > 2°        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Step 7: DPI Normalize │
                    │ Resize to 300 DPI     │
                    │ if below threshold    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Processed Image     │
                    │   (ready for OCR)     │
                    └──────────────────────┘
```

### 7.2 ImagePreprocessor Implementation

```python
class ImagePreprocessor:
    """Preprocess images to improve OCR accuracy."""

    MIN_DPI = 200
    TARGET_DPI = 300
    MAX_SKEW_ANGLE = 2.0

    @staticmethod
    def preprocess(image: Image.Image) -> Image.Image:
        """Run full preprocessing pipeline."""
        img = ImagePreprocessor._correct_orientation(image)
        img = ImagePreprocessor._convert_grayscale(img)
        img = ImagePreprocessor._denoise(img)
        img = ImagePreprocessor._enhance_contrast(img)
        img = ImagePreprocessor._binarize(img)
        img = ImagePreprocessor._deskew(img)
        img = ImagePreprocessor._normalize_dpi(img)
        return img

    @staticmethod
    def _correct_orientation(image: Image.Image) -> Image.Image:
        """Rotate based on EXIF orientation tag."""
        try:
            exif = image.getexif()
            orientation = exif.get(0x0112, 1)
            rotations = {3: 180, 6: 270, 8: 90}
            if orientation in rotations:
                return image.rotate(rotations[orientation], expand=True)
        except Exception:
            pass
        return image

    @staticmethod
    def _convert_grayscale(image: Image.Image) -> Image.Image:
        """Convert to single-channel grayscale."""
        return image.convert("L") if image.mode != "L" else image

    @staticmethod
    def _denoise(image: Image.Image) -> Image.Image:
        """Apply median filter to remove salt-and-pepper noise."""
        return image.filter(ImageFilter.MedianFilter(size=3))

    @staticmethod
    def _enhance_contrast(image: Image.Image) -> Image.Image:
        """Apply CLAHE-like contrast enhancement."""
        img_array = numpy.array(image)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img_array)
        return Image.fromarray(enhanced)

    @staticmethod
    def _binarize(image: Image.Image) -> Image.Image:
        """Apply adaptive thresholding."""
        img_array = numpy.array(image)
        binary = cv2.adaptiveThreshold(
            img_array, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2,
        )
        return Image.fromarray(binary)

    @staticmethod
    def _deskew(image: Image.Image) -> Image.Image:
        """Detect and correct text skew."""
        img_array = numpy.array(image)
        coords = numpy.column_stack(numpy.where(img_array < 255))
        if len(coords) < 100:  # Too few text pixels
            return image
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > ImagePreprocessor.MAX_SKEW_ANGLE:
            (h, w) = img_array.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img_array, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return Image.fromarray(rotated)
        return image

    @staticmethod
    def _normalize_dpi(image: Image.Image) -> Image.Image:
        """Ensure minimum DPI for good OCR."""
        dpi = image.info.get("dpi", (72, 72))
        if dpi[0] < ImagePreprocessor.MIN_DPI:
            scale = ImagePreprocessor.TARGET_DPI / dpi[0]
            new_size = (int(image.width * scale), int(image.height * scale))
            return image.resize(new_size, Image.LANCZOS)
        return image

    @staticmethod
    def convert_pdf_to_images(pdf_path: Path, dpi: int = 300) -> list[Image.Image]:
        """Convert PDF pages to PIL Images."""
        from pdf2image import convert_from_path
        return convert_from_path(pdf_path, dpi=dpi)
```

### 7.3 Preprocessing Cost-Benefit

| Step | Accuracy Improvement | Compute Cost | Always Apply? |
|------|---------------------|--------------|---------------|
| Orientation correction | High (avoids garbage OCR) | Low | Yes |
| Grayscale conversion | Medium (essential for OCR) | Low | Yes |
| Denoise (median filter) | Medium (noise reduction) | Low | Yes |
| CLAHE contrast | High (poor scans benefit greatly) | Medium | Yes |
| Binarization | Medium (good for clean text, bad for handwriting) | Low | No — only for typed text |
| Deskew | High (even 2° skew drops accuracy) | Medium | Yes |
| DPI normalization | High (sub-200 DPI = poor OCR) | High (upscaling) | Yes, if < 200 DPI |

---

## 8. Chunking

### 8.1 Chunking Strategy

The system uses **recursive character splitting** with semantic boundary awareness,
not fixed token counts. Chunks align with document structure (paragraphs, sections,
headers) to preserve context.

### 8.2 Chunking Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size target | 500 tokens (~375 words) | Balances granularity with context |
| Chunk overlap | 50 tokens (~38 words) | Prevents context splitting at boundaries |
| Min chunk size | 100 tokens | Avoids too-small fragments |
| Max chunk size | 1000 tokens | Hard ceiling for embedding model limits |
| Separator priority | `\n\n` → `\n` → `. ` → `; ` → ` ` | Respects document structure |

### 8.3 Chunking Algorithm

```python
class DocumentChunker:
    """Split OCR text into overlapping chunks aligned with document structure."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.separators = ["\n\n", "\n", ". ", "; ", " "]

    def chunk(self, text: str, metadata: dict) -> list[DocumentChunk]:
        """Split text into chunks with metadata."""
        if not text.strip():
            return []

        # Phase 1: Split into semantic sections by headers
        sections = self._split_by_headers(text)

        # Phase 2: Recursively chunk each section
        chunks = []
        for section_text, section_meta in sections:
            section_chunks = self._recursive_split(section_text)
            for i, chunk_text in enumerate(section_chunks):
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    metadata={
                        **metadata,
                        **section_meta,
                        "chunk_index": i,
                        "chunk_count": len(section_chunks),
                    },
                    token_count=self._count_tokens(chunk_text),
                ))

        return chunks

    def _split_by_headers(self, text: str) -> list[tuple[str, dict]]:
        """Split document by markdown-like headers or numbered sections."""
        header_pattern = re.compile(r"^(#{1,3}\s+|(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:))", re.MULTILINE)
        sections = []
        current_header = "preamble"
        current_text = []

        for line in text.split("\n"):
            match = header_pattern.match(line)
            if match:
                if current_text:
                    sections.append(("\n".join(current_text), {"section": current_header}))
                current_header = line.strip().rstrip(":").lstrip("# ")
                current_text = []
            else:
                current_text.append(line)

        if current_text:
            sections.append(("\n".join(current_text), {"section": current_header}))

        return sections

    def _recursive_split(self, text: str) -> list[str]:
        """Recursively split text using the separator hierarchy."""
        if self._count_tokens(text) <= self.chunk_size:
            return [text]

        for separator in self.separators:
            if separator in text:
                splits = text.split(separator)
                # Try to merge smaller splits
                merged = self._merge_splits(splits, separator)
                if len(merged) > 1:
                    return merged

        # Fallback: split by token count
        return self._split_by_tokens(text)

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge small splits back together until target chunk size."""
        chunks = []
        current = []

        for split in splits:
            split_tokens = self._count_tokens(split)
            current_tokens = self._count_tokens(separator.join(current))

            if current_tokens + split_tokens > self.chunk_size and current:
                # Apply overlap to next chunk
                overlap_text = self._get_overlap(current, separator)
                chunks.append(separator.join(current))
                current = [overlap_text] if overlap_text else []

            current.append(split)

        if current:
            remainder = separator.join(current)
            if self._count_tokens(remainder) >= self.min_chunk_size:
                chunks.append(remainder)
            elif chunks:
                # Append small remainder to last chunk
                chunks[-1] += separator + remainder

        return chunks

    def _get_overlap(self, current_chunk: list[str], separator: str) -> str:
        """Extract overlap text from the end of a chunk."""
        full = separator.join(current_chunk)
        tokens = full.split()
        overlap_tokens = tokens[-self.chunk_overlap:] if len(tokens) > self.chunk_overlap else tokens
        return " ".join(overlap_tokens)

    def _split_by_tokens(self, text: str) -> list[str]:
        """Token-based fallback splitting."""
        tokens = text.split()
        chunks = []
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunks.append(" ".join(chunk_tokens))
        return chunks

    def _count_tokens(self, text: str) -> int:
        """Approximate token count (4 chars ≈ 1 token)."""
        return len(text) // 4
```

### 8.4 Chunk Metadata Schema

```python
@dataclass
class DocumentChunk:
    text: str
    metadata: ChunkMetadata
    token_count: int

@dataclass
class ChunkMetadata:
    report_id: str                          # FK to reports table
    patient_id: str                         # FK to patients table
    document_type: str                      # "prescription" | "lab_result" | "discharge_summary"
    section: str                            # Header/section name within document
    chunk_index: int                        # Position in document
    chunk_count: int                        # Total chunks for this document
    upload_date: str                        # ISO date of upload
    original_filename: str                  # User-friendly filename
    page_number: int | None                 # Source page (if multi-page document)
    ocr_confidence: float                   # OCR confidence for this chunk's source
```

### 8.5 When to Chunk

| Document Type | Chunk? | Reason |
|---------------|--------|--------|
| Prescription (short) | No — keep as single chunk | Typically 50-200 tokens |
| Lab result (long) | Yes | Often multi-page with distinct sections |
| Discharge summary (long) | Yes | Multiple sections (medications, follow-up, instructions) |
| Chat history | No — use conversation window | Different retrieval strategy |
| Doctor notes (long) | Yes | Free-form, multi-topic |

---

## 9. Medical Entity Extraction

### 9.1 Extraction Pipeline

```
                   ┌────────────────────────────┐
                   │    OCR Raw Text             │
                   │    (cleaned, assembled)     │
                   └────────────┬───────────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │   Step 1: Classify document type     │
              │   (prescription / lab / discharge)   │
              │   via keyword matching + LLM         │
              └────────────────┬────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
   ┌─────────────────────┐          ┌─────────────────────┐
   │ Prescription/        │          │ Lab Result           │
   │ Discharge Summary    │          │                      │
   └──────────┬──────────┘          └──────────┬──────────┘
              │                                 │
              ▼                                 ▼
   ┌─────────────────────┐          ┌─────────────────────┐
   │ Step 2: Report       │          │ Store raw text,     │
   │ Analysis Prompt      │          │ mark as "lab_result" │
   │ (report_analysis.md) │          │ for later retrieval  │
   └──────────┬──────────┘          └──────────────────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Step 3: Medicine     │
   │ Extraction Prompt    │
   │ (medicine_extraction │
   │  .md)                │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Step 4: Diagnosis    │
   │ Check Prompt         │
   │ (diagnosis_check.md) │
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │ Step 5: Validate &   │
   │ Structure Output     │
   └─────────────────────┘
```

### 9.2 Document Type Classification

```python
class DocumentClassifier:
    """Classify OCR text into document type."""

    PRESCRIPTION_KEYWORDS = ["rx", "prescription", "sig:", "take", "mg", "tablet", "capsule"]
    LAB_KEYWORDS = ["lab", "test result", "hba1c", "ldl", "hdl", "cholesterol", "glucose"]
    DISCHARGE_KEYWORDS = ["discharge summary", "discharge instructions", "follow-up", "hospital course"]

    def classify(self, text: str) -> str:
        """Classify document type based on keyword presence + LLM verification."""
        text_lower = text.lower()

        scores = {
            "prescription": sum(1 for kw in self.PRESCRIPTION_KEYWORDS if kw in text_lower),
            "lab_result": sum(1 for kw in self.LAB_KEYWORDS if kw in text_lower),
            "discharge_summary": sum(1 for kw in self.DISCHARGE_KEYWORDS if kw in text_lower),
        }

        predicted = max(scores, key=scores.get)
        return predicted if scores[predicted] >= 2 else "unknown"
```

### 9.3 LLM Extraction Flow

```python
class MedicalExtractor:
    """Extract structured medical data from OCR text."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.prompt_loader = PromptLoader

    async def extract(self, text: str, document_type: str) -> ExtractionResult:
        """Run the full extraction pipeline."""
        if document_type == "prescription":
            return await self._extract_prescription(text)
        elif document_type == "discharge_summary":
            return await self._extract_discharge(text)
        elif document_type == "lab_result":
            return await self._extract_lab_result(text)
        else:
            # Unknown type — try general extraction
            return await self._extract_general(text)

    async def _extract_prescription(self, text: str) -> ExtractionResult:
        """Full extraction for prescriptions."""
        # Step 1: Report analysis
        report_prompt = self.prompt_loader.load("medical/report_analysis")
        report_result = await self.llm.complete(
            report_prompt.render(text=text),
            agent_type="medical",
            response_format={"type": "json_object"},
        )
        report_data = json.loads(report_result)

        # Step 2: Detailed medicine parsing
        med_prompt = self.prompt_loader.load("medical/medicine_extraction")
        med_text = self._extract_medicine_block(text)
        med_result = await self.llm.complete(
            med_prompt.render(medicine_text=med_text, known_disease=report_data.get("disease", "")),
            agent_type="medical",
            response_format={"type": "json_object"},
        )
        med_data = json.loads(med_result)

        # Step 3: Consistency check
        check_prompt = self.prompt_loader.load("medical/diagnosis_check")
        check_result = await self.llm.complete(
            check_prompt.render(
                extracted_disease=report_data.get("disease", ""),
                raw_text=text,
                medicines=[m.get("name", "") for m in med_data.get("medicines", [])],
            ),
            agent_type="medical",
            response_format={"type": "json_object"},
        )
        check_data = json.loads(check_result)

        return ExtractionResult(
            disease=report_data.get("disease", ""),
            medicines=med_data.get("medicines", []),
            follow_up_date=report_data.get("follow_up_date"),
            doctor_instructions=report_data.get("doctor_instructions", ""),
            notes=report_data.get("notes", ""),
            consistency=check_data,
            confidence=check_data.get("confidence", "low"),
            document_type="prescription",
        )
```

### 9.4 Extraction Result Schema

```python
@dataclass
class ExtractionResult:
    disease: str
    medicines: list[dict]                      # [{name, dosage, frequency, duration, route, instructions}]
    follow_up_date: str | None
    doctor_instructions: str
    notes: str
    consistency: dict                          # Output from diagnosis_check prompt
    confidence: str                            # "high" | "medium" | "low"
    document_type: str
```

### 9.5 Extraction Validation

| Check | Rule | Action on Failure |
|-------|------|-------------------|
| Confidence threshold | Must be ≥ "medium" | Flag for human review |
| Disease-text consistency | `diagnosis_check` must pass | Re-run extraction with different prompt |
| Medicine names | Must exist in text (string match) | Remove hallucinated medicines |
| Dosage format | Must include numeric value + unit | Flag for manual correction |
| Date format | follow_up_date must be YYYY-MM-DD or null | Attempt to parse, null if impossible |

---

## 10. Medicine Parsing

### 10.1 Parsing Strategy

After the LLM extracts structured medicine data from the full report, a
**dedicated parsing pass** normalizes each medicine entry into the database schema.

### 10.2 Medicine Normalizer

```python
class MedicineNormalizer:
    """Normalize extracted medicine data into database-ready format."""

    ROUTE_ALIASES = {
        "po": "oral",
        "by mouth": "oral",
        "orally": "oral",
        "top": "topical",
        "iv": "intravenous",
        "im": "intramuscular",
        "sc": "subcutaneous",
        "subq": "subcutaneous",
        "inh": "inhalation",
        "sl": "sublingual",
    }

    FREQUENCY_ALIASES = {
        "qd": "once daily",
        "od": "once daily",
        "bid": "twice daily",
        "tid": "three times daily",
        "qid": "four times daily",
        "qhs": "at bedtime",
        "qam": "in the morning",
        "qpm": "in the evening",
        "prn": "as needed",
    }

    def normalize(self, raw_medicines: list[dict], report_id: str, patient_id: str) -> list[NormalizedMedicine]:
        """Convert raw LLM extraction to database-ready medicine records."""
        normalized = []
        for med in raw_medicines:
            normalized.append(NormalizedMedicine(
                report_id=report_id,
                patient_id=patient_id,
                name=med.get("name", "unknown").strip().title(),
                dosage=self._normalize_dosage(med.get("dosage", "")),
                frequency=self._normalize_frequency(med.get("frequency", "")),
                duration=med.get("duration"),
                route=self._normalize_route(med.get("route", "oral")),
                instructions=med.get("instructions", ""),
                start_date=med.get("start_date"),
                end_date=med.get("end_date"),
                is_active=True,
            ))
        return normalized

    def _normalize_dosage(self, dosage: str) -> str:
        """Standardize dosage format."""
        dosage = dosage.strip().lower()
        dosage = re.sub(r"\s+", " ", dosage)
        dosage = re.sub(r"(\d+)\s*(mg|mcg|g|ml|iu)", r"\1\2", dosage)
        return dosage

    def _normalize_frequency(self, frequency: str) -> str:
        """Convert abbreviated frequencies to full text."""
        freq_lower = frequency.strip().lower()
        return self.FREQUENCY_ALIASES.get(freq_lower, frequency)

    def _normalize_route(self, route: str) -> str:
        """Convert route aliases to standard values."""
        route_lower = route.strip().lower()
        return self.ROUTE_ALIASES.get(route_lower, route_lower)
```

### 10.3 Deduplication Logic

Before inserting medicines, check for duplicates with existing active medicines
for the same patient:

```python
async def deduplicate_medicines(
    db: AsyncSession,
    patient_id: str,
    new_medicines: list[NormalizedMedicine],
) -> list[NormalizedMedicine]:
    """Remove medicines that already exist as active for this patient."""
    existing = await medicine_repo.get_active_by_patient(db, patient_id)

    def is_duplicate(new: NormalizedMedicine, existing_list: list) -> bool:
        for existing_med in existing_list:
            if (new.name.lower() == existing_med.name.lower()
                    and new.dosage == existing_med.dosage
                    and new.frequency == existing_med.frequency):
                return True
        return False

    return [m for m in new_medicines if not is_duplicate(m, existing)]
```

### 10.4 Medicine Validation Rules

| Rule | Description |
|------|-------------|
| Name required | Every medicine must have a name |
| Dosage unit required | `500` → reject, `500mg` → accept |
| Frequency required | At minimum a vague frequency ("daily") |
| Route must be valid | Must match `MedicineRoute` enum or alias |
| Date range valid | `end_date ≥ start_date` (if both present) |
| No future start_date | `start_date` cannot be > 30 days in the future (suspicious) |

---

## 11. JSON Validation

### 11.1 Validation Pipeline

```
LLM Raw Output (string)
    │
    ▼
┌─────────────────────────────────────┐
│  Step 1: Extract JSON                │
│  • Strip markdown fences (```json)   │
│  • Find first { and last }           │
│  • Attempt json.loads()              │
│  • On failure: attempt repair        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 2: Schema Validation           │
│  • Validate against expected schema  │
│  • Check required fields present     │
│  • Check types match                 │
│  • Check enum values are valid       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 3: Repair                     │
│  • Missing required → null/empty    │
│  • Wrong type → coerce              │
│  • Invalid enum → closest match     │
│  • Extra fields → preserve          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 4: Business Validation        │
│  • OCR text contains medicine names │
│  • Dosage has units                 │
│  • Dates are parseable              │
│  • No blacklisted terms             │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ▼              ▼
   Valid JSON     Invalid JSON
        │              │
        ▼              ▼
   Store in DB    Set status = failed
                  Log validation errors
```

### 11.2 SchemaLoader

```python
class SchemaLoader:
    """Load and cache JSON schemas from prompts/schemas/."""

    _cache: dict[str, dict] = {}

    @classmethod
    def load(cls, prompt_path: str) -> dict:
        """Load JSON schema for a given prompt path."""
        if prompt_path in cls._cache:
            return cls._cache[prompt_path]

        schema_path = Path(__file__).parent.parent / "prompts" / "schemas" / f"{prompt_path.replace('/', '_')}.json"
        if schema_path.exists():
            with open(schema_path) as f:
                schema = json.load(f)
        else:
            # Fallback: build schema from prompt metadata defaults
            schema = cls._build_from_metadata(prompt_path)

        cls._cache[prompt_path] = schema
        return schema
```

### 11.3 Repair Strategies

```python
class JSONRepair:
    """Repair common JSON issues from LLM outputs."""

    @staticmethod
    def extract_json(text: str) -> str:
        """Extract JSON object from arbitrary text."""
        # Remove markdown fences
        text = re.sub(r"```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```", "", text)

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise JSONExtractionError("No JSON object found in response")
        return text[start:end + 1]

    @staticmethod
    def repair_enum(value: str, allowed_values: list[str]) -> str:
        """Find closest match for an invalid enum value."""
        if value in allowed_values:
            return value
        # Try case-insensitive
        for allowed in allowed_values:
            if value.lower() == allowed.lower():
                return allowed
        # Try substring match
        for allowed in allowed_values:
            if value.lower() in allowed.lower() or allowed.lower() in value.lower():
                return allowed
        return allowed_values[0]  # Default to first

    @staticmethod
    def coerce_type(value: Any, expected_type: str) -> Any:
        """Attempt type coercion."""
        if expected_type == "array" and not isinstance(value, list):
            return [value]
        if expected_type == "object" and not isinstance(value, dict):
            return {}
        if expected_type == "number":
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0
        if expected_type == "integer":
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0
        if expected_type == "string" and not isinstance(value, str):
            return str(value)
        return value
```

### 11.4 Validation Result

```python
@dataclass
class ValidationResult:
    is_valid: bool
    data: dict | None
    errors: list[ValidationError]
    warnings: list[str]
    was_repaired: bool
    repair_log: list[str]

@dataclass
class ValidationError:
    path: str               # JSON path, e.g., "medicines[0].dosage"
    message: str
    severity: str           # "error" | "warning"
```

---

## 12. Database Storage

### 12.1 Storage Flow

```
                    ┌──────────────────────────────┐
                    │  ExtractionResult (validated) │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  1. Update Report record      │
                    │  • ocr_text = raw text        │
                    │  • extracted_data = full JSON │
                    │  • status = "completed"       │
                    │  • processed_at = now()       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  2. Create Medicine records   │
                    │  • One per extracted medicine │
                    │  • report_id FK to Report     │
                    │  • patient_id FK to Patient   │
                    │  • is_active = true           │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  3. Return to caller          │
                    │  • report_id                  │
                    │  • medicine_count             │
                    │  • confidence                 │
                    └──────────────────────────────┘
```

### 12.2 Database Transaction

```python
async def store_extraction_results(
    db: AsyncSession,
    report_id: str,
    patient_id: str,
    ocr_text: str,
    extraction: ExtractionResult,
    normalized_medicines: list[NormalizedMedicine],
) -> StoreResult:
    """Store extraction results in a single DB transaction."""
    async with db.begin():
        # 1. Update report
        report = await report_repo.get(db, report_id)
        report.ocr_text = ocr_text
        report.extracted_data = {
            "disease": extraction.disease,
            "follow_up_date": extraction.follow_up_date,
            "doctor_instructions": extraction.doctor_instructions,
            "notes": extraction.notes,
            "confidence": extraction.confidence,
            "consistency": extraction.consistency,
        }
        report.status = "completed"
        report.processed_at = datetime.now(timezone.utc)

        # 2. Create medicine records
        created_medicines = []
        for med in normalized_medicines:
            medicine = Medicine(
                report_id=report_id,
                patient_id=patient_id,
                name=med.name,
                dosage=med.dosage,
                frequency=med.frequency,
                duration=med.duration,
                route=med.route,
                instructions=med.instructions,
                start_date=med.start_date,
                end_date=med.end_date,
                is_active=True,
            )
            db.add(medicine)
            created_medicines.append(medicine)

        await db.flush()

    return StoreResult(
        report_id=report_id,
        medicine_count=len(created_medicines),
        medicine_ids=[str(m.id) for m in created_medicines],
        confidence=extraction.confidence,
    )
```

### 12.3 Storage Error Scenarios

| Scenario | Handling |
|----------|----------|
| DB connection lost during store | Transaction rollback → retry from queue |
| Report not found (deleted during processing) | Abort, delete orphaned files, log audit |
| Medicine FK violation | Likely report_id mismatch — abort, investigate |
| Duplicate medicine (same name/dosage/frequency) | Skip duplicate, log warning, continue |
| Partial write (one medicine fails) | Transaction atomic — all or nothing |

### 12.4 Post-Storage Side Effects

After successful storage, the pipeline triggers:

1. **Background embedding** (Stage 4 — see section 13)
2. **Reminder agent update** — new medicines may affect adherence schedules
3. **Patient notification** — if auto-processing completed successfully
4. **Doctor notification** — if extraction confidence is low

---

## 13. Embedding Creation

### 13.1 Embedding Strategy

| Property | Value |
|----------|-------|
| Model | `text-embedding-3-small` (OpenAI) |
| Dimensions | 1536 |
| Max tokens per chunk | 8191 |
| Batch size | 20 chunks per API call |
| Cost | $0.02/1K tokens (input) |

### 13.2 Embedding Service

```python
class EmbeddingService:
    """Generate embeddings for document chunks."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.CHOORA_EMBEDDING_MODEL

    async def embed_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentEmbedding]:
        """Generate embeddings for a batch of chunks."""
        texts = [c.text for c in chunks]
        embeddings = await self._embed_batch(texts)

        return [
            DocumentEmbedding(
                chunk_index=chunks[i].metadata.chunk_index,
                text=chunks[i].text,
                embedding=embeddings[i],
                metadata=chunks[i].metadata,
            )
            for i in range(len(chunks))
        ]

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        response = await self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        return response.data[0].embedding

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in one API call."""
        # Split into batches of 20
        all_embeddings = []
        for i in range(0, len(texts), 20):
            batch = texts[i:i + 20]
            response = await self.client.embeddings.create(
                input=batch,
                model=self.model,
            )
            all_embeddings.extend([r.embedding for r in response.data])
        return all_embeddings
```

### 13.3 Embedding Quality Checks

| Check | Threshold | Action |
|-------|-----------|--------|
| Embedding norm | > 0.001 | Reject zero/near-zero embeddings |
| Embedding dimension | == 1536 | Log error, skip chunk |
| Text non-empty | > 0 chars | Skip empty chunks |
| Chunk token count | ≤ 8191 | Truncate if exceeded |

### 13.4 Embedding Cost Tracking

```python
@dataclass
class EmbeddingCost:
    chunk_count: int
    total_tokens: int
    cost_usd: float
    model: str
```

---

## 14. Vector Database

### 14.1 ChromaDB Configuration

| Property | Development | Production |
|----------|-------------|------------|
| Host | `localhost` | ChromaDB cluster |
| Port | 8001 | 8001 |
| Collection | `report_embeddings` | `report_embeddings` |
| Embedding function | `text-embedding-3-small` | same |
| Distance metric | `cosine` | `cosine` |
| Persistence | In-memory | Disk + S3 backup |

### 14.2 Collection Schema

```python
class VectorCollection:
    """Manage ChromaDB collection operations."""

    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        self.collection_name = settings.CHROMA_COLLECTION_NAME

    async def get_or_create_collection(self) -> chromadb.Collection:
        """Get or create the document embeddings collection."""
        try:
            return self.client.get_collection(self.collection_name)
        except ValueError:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    async def add_embeddings(self, embeddings: list[DocumentEmbedding]) -> list[str]:
        """Add embeddings to the vector store."""
        collection = await self.get_or_create_collection()

        ids = []
        vectors = []
        metadatas = []
        documents = []

        for emb in embeddings:
            chunk_id = f"{emb.metadata.report_id}_chunk_{emb.chunk_index}"
            ids.append(chunk_id)
            vectors.append(emb.embedding)
            documents.append(emb.text)
            metadatas.append({
                "report_id": emb.metadata.report_id,
                "patient_id": emb.metadata.patient_id,
                "document_type": emb.metadata.document_type,
                "section": emb.metadata.section,
                "chunk_index": emb.chunk_index,
                "chunk_count": emb.metadata.chunk_count,
                "upload_date": emb.metadata.upload_date,
                "original_filename": emb.metadata.original_filename,
                "ocr_confidence": emb.metadata.ocr_confidence,
            })

        collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas,
            documents=documents,
        )

        return ids
```

### 14.3 Vector IDs Format

```
{report_id}_chunk_{chunk_index}
```

Example: `a1b2c3d4-..._chunk_0`

### 14.4 Metadata Filterable Fields

All stored as ChromaDB metadata for filtered search:

```python
METADATA_FILTERS = {
    "patient_id": str,         # Exact match — scope to patient
    "document_type": str,      # Exact match — filter by type
    "report_id": str,          # Exact match — source document
    "upload_date": str,        # Range query — recency filter
    "section": str,            # Exact match — specific section
    "ocr_confidence": float,   # Range query — quality filter
}
```

### 14.5 Vector Store Operations

| Operation | Implemented | Notes |
|-----------|-------------|-------|
| Add embeddings | Yes | After document processing |
| Search by vector | Yes | Cosine similarity, top-k |
| Filter by patient_id | Yes | Must always filter to patient |
| Delete by report_id | Yes | When report is deleted |
| Delete by patient_id | Yes | GDPR/data deletion requests |
| Update embedding | No | Re-add with same ID (overwrite) |
| List collections | Yes | Admin operations |

### 14.6 Data Deletion Policy

```python
async def delete_report_vectors(report_id: str):
    """Delete all vectors for a given report."""
    collection = await vector_store.get_or_create_collection()
    # ChromaDB supports prefix-based deletion
    collection.delete(where={"report_id": report_id})

async def delete_patient_vectors(patient_id: str):
    """Delete all vectors for a given patient (GDPR)."""
    collection = await vector_store.get_or_create_collection()
    collection.delete(where={"patient_id": patient_id})
```

---

## 15. RAG

### 15.1 RAG Pipeline

```
                    ┌────────────────────────────┐
                    │  Patient Question           │
                    │  (input to Chat Agent)      │
                    └────────────┬───────────────┘
                                 │
                                 ▼
              ┌────────────────────────────────────┐
              │  Step 1: Query Generation           │
              │  Prompt: rag/document_retrieval.md  │
              │  Output: search queries + filters   │
              └────────────────┬───────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────┐
              │  Step 2: Vector Search              │
              │  For each search query:            │
              │  • Embed query                     │
              │  • ChromaDB similarity search      │
              │  • Filter: patient_id              │
              │  • Top-k: 10 per query             │
              └────────────────┬───────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────┐
              │  Step 3: Merge & Deduplicate        │
              │  • Merge results from all queries   │
              │  • Deduplicate by chunk_id          │
              │  • Sort by score descending         │
              └────────────────┬───────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────┐
              │  Step 4: Context Compression        │
              │  Prompt: rag/context_compression.md │
              │  Output: compressed context +       │
              │  sources list                       │
              └────────────────┬───────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────┐
              │  Step 5: Response Generation        │
              │  Prompt: chat/patient_chat.md       │
              │  Context: compressed_context        │
              └────────────────┬───────────────────┘
                               │
                               ▼
              ┌────────────────────────────────────┐
              │  Step 6: Citation Formatting        │
              │  Prompt: rag/citation_format.md     │
              │  Output: response with [1], [2]    │
              └────────────────────────────────────┘
```

### 15.2 Retriever Implementation

```python
class Retriever:
    """Retrieve relevant document chunks for a patient question."""

    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embeddings = embedding_service

    async def retrieve(
        self,
        question: str,
        patient_id: str,
        top_k: int = 10,
        document_types: list[str] | None = None,
    ) -> RetrievalResult:
        """Retrieve relevant chunks for a patient question."""
        # Step 1: Generate search queries
        search_queries = await self._generate_queries(question, patient_id)

        # Step 2: Search vector store for each query
        all_results = []
        for query in search_queries:
            query_embedding = await self.embeddings.embed_text(query)
            results = await self.vector_store.search(
                embedding=query_embedding,
                top_k=top_k,
                filter_dict={"patient_id": patient_id},
            )
            all_results.extend(results)

        # Step 3: Deduplicate and sort
        unique_results = self._deduplicate(all_results)
        sorted_results = sorted(unique_results, key=lambda r: r.score, reverse=True)

        # Step 4: Compress context
        compressed = await self._compress_context(question, sorted_results[:top_k])

        return RetrievalResult(
            chunks=sorted_results[:top_k],
            compressed_context=compressed.compressed_context,
            sources=compressed.sources,
            dropped_chunks=compressed.dropped_chunks,
            query_count=len(search_queries),
        )

    def _deduplicate(self, results: list[SearchResult]) -> list[SearchResult]:
        """Remove duplicate chunks (same chunk_id) keeping highest score."""
        seen: dict[str, SearchResult] = {}
        for r in results:
            chunk_id = f"{r.metadata['report_id']}_chunk_{r.metadata['chunk_index']}"
            if chunk_id not in seen or r.score > seen[chunk_id].score:
                seen[chunk_id] = r
        return list(seen.values())

    async def _generate_queries(self, question: str, patient_id: str) -> list[str]:
        """Use LLM to generate optimized search queries."""
        prompt = PromptLoader.load("rag/document_retrieval")
        rendered = prompt.render(
            question=question,
            patient_id=patient_id,
            conversation_history=[],
        )
        response = await llm_client.complete(rendered, agent_type="rag", response_format={"type": "json_object"})
        data = json.loads(response)
        return data.get("search_queries", [question])

    async def _compress_context(self, question: str, chunks: list[SearchResult]) -> CompressionResult:
        """Compress and prioritize retrieved chunks."""
        prompt = PromptLoader.load("rag/context_compression")
        rendered = prompt.render(
            question=question,
            retrieved_chunks=[{"text": c.text, "score": c.score, "metadata": c.metadata} for c in chunks],
            max_tokens=3000,
        )
        response = await llm_client.complete(rendered, agent_type="rag", response_format={"type": "json_object"})
        return CompressionResult(**json.loads(response))
```

### 15.3 Filtering Rules

| Filter | Scope | Implementation |
|--------|-------|---------------|
| Patient isolation | Always | `patient_id` filter on every search |
| Document type | Optional | `document_type` filter (prescription vs lab) |
| Date range | Optional | `upload_date >= start_date AND <= end_date` |
| Recency boost | Default | Results within 30 days get +0.1 score boost |

### 15.4 RAG Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Retrieval precision | > 80% | % of retrieved chunks relevant to question |
| Context utilization | > 70% | % of compressed context used in final response |
| Citation accuracy | > 95% | % of citations correctly supporting the claim |
| Fallback rate | < 5% | % of questions answered without retrieved context |

---

## 16. Failure Recovery

### 16.1 Failure Taxonomy for Document Pipeline

| Failure | Stage | Detectability | Recovery |
|---------|-------|---------------|----------|
| File too large | Upload | Immediate | Return 400 |
| Invalid file type | Upload | Immediate | Return 400 |
| Corrupted file | Validation | Immediate | Return 422 |
| Virus detected | Scan | Immediate | Delete file, log security event |
| OCR service down | OCR | Timeout (10s) | Fallback to Tesseract |
| OCR low confidence | OCR | After OCR completes | Flag for human review |
| LLM timeout | Extraction | Timeout (15s) | Retry 2x, then fallback model |
| LLM malformed JSON | Extraction | After response | Retry with stricter prompt |
| ChromaDB unavailable | Indexing | Connection error | Retry 3x, then log and skip |
| DB connection lost | Storage | Transaction failure | Retry from queue |

### 16.2 State Recovery

Each stage saves intermediate results so the pipeline can resume:

```python
class PipelineRecovery:
    """Recovery checkpoints for each pipeline stage."""

    STAGE_CHECKPOINTS = {
        "upload": ["report_id", "file_path", "file_type"],
        "validation": ["report_id", "validation_result"],
        "virus_scan": ["report_id", "scan_result"],
        "ocr": ["report_id", "ocr_text", "ocr_confidence", "pages"],
        "extraction": ["report_id", "disease", "medicines", "confidence"],
        "storage": ["report_id", "medicine_ids", "stored_at"],
        "indexing": ["report_id", "vector_ids", "chunk_count"],
    }

    async def get_checkpoint(self, report_id: str, stage: str) -> dict | None:
        """Retrieve checkpoint data for a given stage."""
        task = await pipeline_task_repo.get_by_report_and_stage(report_id, stage)
        if task and task.status == "completed":
            return task.checkpoint_data
        return None

    async def save_checkpoint(self, report_id: str, stage: str, data: dict):
        """Save checkpoint data after a stage completes."""
        await pipeline_task_repo.upsert(
            report_id=report_id,
            stage=stage,
            status="completed",
            checkpoint_data=data,
        )

    async def can_resume_from(self, report_id: str) -> str | None:
        """Determine which stage to resume from."""
        stages = ["upload", "validation", "virus_scan", "ocr", "extraction", "storage", "indexing"]
        for stage in reversed(stages):
            checkpoint = await self.get_checkpoint(report_id, stage)
            if checkpoint:
                next_idx = stages.index(stage) + 1
                if next_idx < len(stages):
                    return stages[next_idx]
        return "upload"  # Start from beginning
```

### 16.3 Graceful Degradation

| Component Down | Effect | User Experience |
|---------------|--------|----------------|
| Google Vision API | Fallback to Tesseract | Processing slower, potentially lower quality |
| All OCR services | Pipeline pauses | Report stays in "pending" status |
| OpenAI API | No extraction, no vector search | Report stays in "ocr_done"; chat falls back |
| ChromaDB | No vector search | Chat answers without RAG context |
| Database | Everything stops | All operations fail |

---

## 17. Background Processing

### 17.1 Processing Model

The document pipeline uses **background task processing** — the upload endpoint
returns immediately, and processing happens asynchronously.

```
Upload Request
    │
    ├── Accept file (HTTP 200)
    ├── Create DB record (status="pending")
    ├── Return response to client
    └── Enqueue to pipeline queue
         │
         └── Processor picks up from queue
              │
              ├── Update status to "processing"
              ├── Run pipeline stages
              ├── Update status to "completed" / "failed"
              └── Send notification (optional)
```

### 17.2 Background Worker

```python
class DocumentPipelineWorker:
    """Background worker that processes documents through the pipeline."""

    def __init__(self, queue: PipelineQueue):
        self.queue = queue
        self.logger = structlog.get_logger(__name__)

    async def process_next(self) -> bool:
        """Process the next job from the queue."""
        job = await self.queue.dequeue()
        if not job:
            return False

        self.logger.info("processing_document", report_id=job.report_id)

        try:
            result = await self._run_pipeline(job)
            await self.queue.complete(job.id, result)
            return True
        except Exception as e:
            self.logger.error("pipeline_failed", report_id=job.report_id, error=str(e))
            await self.queue.fail(job.id, str(e))
            return False

    async def _run_pipeline(self, job: PipelineJob) -> PipelineResult:
        """Execute all pipeline stages."""
        recovery = PipelineRecovery()

        # Check if we can resume from a checkpoint
        resume_stage = await recovery.can_resume_from(job.report_id)
        stages = self._get_stages_from(resume_stage)

        for stage_name, stage_fn in stages:
            self.logger.info("running_stage", stage=stage_name, report_id=job.report_id)

            # Update report status
            await self._update_status(job.report_id, stage_name)

            # Run with timeout
            try:
                result = await asyncio.wait_for(
                    stage_fn(job),
                    timeout=STAGE_TIMEOUTS.get(stage_name, 30),
                )
                await recovery.save_checkpoint(job.report_id, stage_name, result)
            except asyncio.TimeoutError:
                raise PipelineStageTimeout(stage_name)
            except Exception as e:
                raise PipelineStageError(stage_name, str(e))

        return PipelineResult(
            report_id=job.report_id,
            status="completed",
            stages_completed=list(STAGES.keys()),
        )
```

### 17.3 Processing Prioritization

```python
class PriorityQueue:
    """Priority queue for pipeline jobs."""

    HIGH = 10       # Emergency reports, doctor-initiated
    NORMAL = 5      # Patient uploads
    LOW = 1         # Batch re-processing, background sync
```

### 17.4 Worker Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Concurrent workers | 3 | Balance throughput vs resource usage |
| Poll interval | 1 second | Quick pickup without busy-waiting |
| Max retries per job | 3 | Prevent infinite retries |
| Job timeout | 5 minutes | Hard limit for any single job |
| Prefetch count | 1 | Avoid holding multiple jobs in memory |

---

## 18. Retry Logic

### 18.1 Retry Configuration Per Stage

| Stage | Max Retries | Backoff | Retryable Errors | Non-Retryable |
|-------|-------------|---------|-----------------|---------------|
| Upload | 0 | — | — | All (deterministic) |
| Validation | 0 | — | — | All |
| Virus Scan | 1 | 5s fixed | Scan timeout | Infected file |
| OCR | 3 | 2^N exp + jitter | API timeout, 500, 429 | Invalid image, corrupted PDF |
| Extraction | 3 | 2^N exp + jitter | LLM timeout, malformed JSON | All LLM attempts exhausted |
| Storage | 2 | 1s fixed | DB connection error | FK violation, constraint error |
| Indexing | 2 | 5s fixed | ChromaDB connection error | Invalid embedding, wrong dimension |

### 18.2 Retry State Machine

```
                    ┌──────────┐
                    │  PENDING │  (initial state)
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
             ┌─────►│ RUNNING  │
             │      └────┬─────┘
             │           │
             │    ┌──────┴──────┐
             │    │              │
             │    ▼              ▼
             │ ┌────────┐  ┌────────┐
             │ │SUCCESS │  │ FAILED │  (non-retryable)
             │ └────────┘  └───┬────┘
             │                 │
             │       ┌─────────┴─────────┐
             │       │                   │
             │  retries_left > 0    retries_left = 0
             │       │                   │
             │       ▼                   ▼
             │  ┌──────────┐       ┌──────────┐
             │  │  RETRY   │       │ EXHAUSTED│
             │  └────┬─────┘       └──────────┘
             │       │
             └───────┘  (re-queue with delay)
```

### 18.3 Retry Queue

```python
class RetryQueue:
    """Manages retry logic with exponential backoff and dead-letter queue."""

    MAX_RETRIES = 3
    BACKOFF_BASE = 2  # seconds
    MAX_BACKOFF = 60  # seconds

    def __init__(self, queue: PipelineQueue):
        self.queue = queue

    async def handle_failure(self, job: PipelineJob, error: str, stage: str) -> None:
        """Determine whether to retry or dead-letter."""
        retries = job.retry_counts.get(stage, 0)

        if retries < self.MAX_RETRIES and self._is_retryable(error):
            await self._schedule_retry(job, stage, retries)
        else:
            await self._dead_letter(job, stage, error)

    async def _schedule_retry(self, job: PipelineJob, stage: str, retries: int) -> None:
        """Re-queue with exponential backoff."""
        delay = min(self.BACKOFF_BASE ** (retries + 1), self.MAX_BACKOFF)
        jitter = random.uniform(0, delay * 0.2)

        job.retry_counts[stage] = retries + 1
        job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay + jitter)

        await self.queue.requeue(job, delay=delay + jitter)
        logger.info(
            "scheduled_retry",
            report_id=job.report_id,
            stage=stage,
            attempt=retries + 1,
            delay_seconds=delay + jitter,
        )

    async def _dead_letter(self, job: PipelineJob, stage: str, error: str) -> None:
        """Move to dead-letter queue after exhausting retries."""
        job.status = "dead_letter"
        job.dead_letter_reason = f"Stage '{stage}' failed after {self.MAX_RETRIES} retries: {error}"
        await self.queue.dead_letter(job)

        await report_repo.update_status(
            job.report_id,
            status="failed",
            error_message=job.dead_letter_reason,
        )

        logger.error(
            "dead_letter",
            report_id=job.report_id,
            stage=stage,
            error=error,
        )

    def _is_retryable(self, error: str) -> bool:
        """Check if an error is retryable."""
        non_retryable_patterns = [
            "virus detected",
            "invalid file",
            "corrupted",
            "permission denied",
            "authentication failed",
            "invalid api key",
        ]
        error_lower = error.lower()
        return not any(pattern in error_lower for pattern in non_retryable_patterns)
```

### 18.4 Dead Letter Queue

When a job exhausts all retries, it goes to the dead-letter queue:

```python
@dataclass
class DeadLetterJob:
    id: str
    report_id: str
    stage: str
    error: str
    retries_attempted: int
    original_payload: dict
    failed_at: str

class DeadLetterQueue:
    """Store permanently failed jobs for manual review."""

    async def list(self) -> list[DeadLetterJob]:
        """List all jobs in the dead-letter queue."""
        ...

    async def replay(self, job_id: str) -> None:
        """Replay a dead-letter job (reset retry count, re-enqueue)."""
        ...

    async def discard(self, job_id: str) -> None:
        """Discard a dead-letter job permanently."""
        ...
```

---

## 19. Queue Architecture

### 19.1 Queue Provider

| Environment | Provider | Implementation |
|-------------|----------|---------------|
| Development | In-memory | `asyncio.Queue` — no persistence, jobs lost on restart |
| Production | Redis | `rq` (Redis Queue) — persistent, supports priorities |
| Production (alternative) | RabbitMQ | `aio-pika` — full AMQP, supports exchanges |

### 19.2 Queue Abstraction

```python
class PipelineQueue(ABC):
    """Abstract queue for pipeline jobs."""

    @abstractmethod
    async def enqueue(self, job: PipelineJob) -> None:
        """Add a job to the queue."""

    @abstractmethod
    async def dequeue(self) -> PipelineJob | None:
        """Get the next job from the queue."""

    @abstractmethod
    async def complete(self, job_id: str, result: PipelineResult) -> None:
        """Mark a job as completed."""

    @abstractmethod
    async def fail(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""

    @abstractmethod
    async def requeue(self, job: PipelineJob, delay: float = 0) -> None:
        """Re-queue a job (for retries)."""

    @abstractmethod
    async def dead_letter(self, job: PipelineJob) -> None:
        """Move a job to the dead-letter queue."""

    @abstractmethod
    async def length(self) -> int:
        """Get the current queue length."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all jobs from the queue."""
```

### 19.3 In-Memory Implementation (Development)

```python
class InMemoryPipelineQueue(PipelineQueue):
    """In-memory queue for development/testing."""

    def __init__(self):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.completed: dict[str, PipelineResult] = {}
        self.failed: dict[str, str] = {}
        self.dead_letter: list[DeadLetterJob] = []

    async def enqueue(self, job: PipelineJob) -> None:
        priority = job.priority
        await self.queue.put((priority, datetime.now(timezone.utc), job))

    async def dequeue(self) -> PipelineJob | None:
        try:
            _, _, job = await asyncio.wait_for(self.queue.get(), timeout=1)
            return job
        except asyncio.TimeoutError:
            return None

    async def complete(self, job_id: str, result: PipelineResult) -> None:
        self.completed[job_id] = result

    async def fail(self, job_id: str, error: str) -> None:
        self.failed[job_id] = error
```

### 19.4 Redis Queue Implementation (Production)

```python
class RedisPipelineQueue(PipelineQueue):
    """Redis-backed queue for production."""

    QUEUE_KEY = "pipeline:queue"
    PROCESSING_KEY = "pipeline:processing"
    DEAD_LETTER_KEY = "pipeline:dead_letter"
    RESULT_KEY = "pipeline:result:{}"

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def enqueue(self, job: PipelineJob) -> None:
        payload = json.dumps(asdict(job), default=str)
        score = self._priority_to_score(job.priority)
        await self.redis.zadd(self.QUEUE_KEY, {payload: score})

    async def dequeue(self) -> PipelineJob | None:
        # Atomic: move from queue to processing
        result = await self.redis.zpopmin(self.QUEUE_KEY)
        if not result:
            return None
        payload = json.loads(result[0][0])
        job = PipelineJob(**payload)

        # Store in processing set (for crash recovery)
        await self.redis.hset(self.PROCESSING_KEY, job.id, result[0][0])
        return job

    def _priority_to_score(self, priority: int) -> float:
        """Convert priority to zset score (lower = higher priority)."""
        return {
            10: 1.0,    # HIGH
            5: 10.0,    # NORMAL
            1: 100.0,   # LOW
        }.get(priority, 10.0)
```

### 19.5 Job Schema

```python
@dataclass
class PipelineJob:
    id: str                                     # UUID
    report_id: str                              # FK to reports
    patient_id: str                             # FK to patients
    file_path: str                              # Path to uploaded file
    file_type: str                              # pdf, jpg, png
    priority: int                               # 1 (LOW) to 10 (HIGH)
    created_at: str                             # ISO timestamp
    retry_counts: dict[str, int] = field(default_factory=dict)  # Per-stage retries
    next_retry_at: str | None = None            # For delayed retries
    status: str = "pending"                     # pending, running, completed, failed, dead_letter
    dead_letter_reason: str | None = None

@dataclass
class PipelineResult:
    report_id: str
    status: str                                  # completed, failed
    stages_completed: list[str]
    error: str | None = None
    medicine_count: int = 0
    chunk_count: int = 0
    total_processing_ms: int = 0
```

### 19.6 Queue Monitoring

```python
class QueueMonitor:
    """Monitor queue health and metrics."""

    async def metrics(self) -> dict:
        return {
            "queue_length": await self.queue.length(),
            "processing_count": len(await self.queue.list_processing()),
            "dead_letter_count": len(await self.queue.list_dead_letter()),
            "completed_today": await self._completed_today(),
            "failed_today": await self._failed_today(),
            "avg_processing_time_ms": await self._avg_processing_time(),
            "p95_processing_time_ms": await self._p95_processing_time(),
        }
```

### 19.7 Queue Cleanup

```python
class QueueCleanup:
    """Periodic cleanup of completed/failed jobs."""

    RETENTION_DAYS = 7

    async def cleanup(self):
        """Remove jobs older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_DAYS)
        await self._cleanup_completed(cutoff)
        await self._cleanup_dead_letter(cutoff)

    async def recover_orphaned(self):
        """Recover jobs stuck in 'processing' state (worker crash)."""
        processing = await self.queue.list_processing()
        for job_id, payload in processing.items():
            job = PipelineJob(**json.loads(payload))
            if self._is_orphaned(job):
                logger.warning(f"Recovering orphaned job: {job_id}")
                await self.queue.requeue(job, delay=5)
```

---

## 20. Architecture Decision Records

### ADR-015: Background Queue over Synchronous Processing
**Status:** Accepted
**Context:** Document processing (OCR + LLM extraction) takes 10-60 seconds. Processing synchronously would block HTTP requests.
**Decision:** Use an async background queue. Upload returns immediately with `report_id`. Client polls for status.
**Rationale:** Synchronous processing would exhaust worker threads, time out proxies, and provide poor UX. A queue allows retries, prioritization, and graceful degradation.

### ADR-016: Google Cloud Vision Primary, Tesseract Fallback
**Status:** Accepted
**Context:** OCR quality directly impacts extraction accuracy. Multiple OCR options exist.
**Decision:** Google Cloud Vision is primary (best accuracy for medical documents). Tesseract is fallback. Direct PDF extraction is tried first for PDFs with text layers.
**Rationale:** Google Vision offers superior handwriting recognition and table extraction, critical for prescriptions. Tesseract provides zero-cost fallback. Direct PDF avoids unnecessary OCR for native digital documents.

### ADR-017: ChromaDB over Pinecone/Weaviate
**Status:** Accepted
**Context:** Vector database selection for RAG.
**Decision:** ChromaDB for development and small-scale production. Migrate to Pinecone or Weaviate if scale requires it.
**Rationale:** ChromaDB is self-hosted, zero-cost, and simple to operate. It meets the expected scale (<1M vectors). The abstract `VectorStore` interface allows swapping providers without code changes.

### ADR-018: Recursive Character Chunking over Semantic Chunking
**Status:** Accepted
**Context:** Document chunking strategy for embeddings.
**Decision:** Use recursive character splitting with header-based pre-splitting. Not semantic chunking (LLM-based boundary detection).
**Rationale:** Semantic chunking adds latency and cost per document. Recursive character splitting with structural boundaries (headers, paragraphs) is sufficient for medical documents that have clear section structure. Semantic chunking can be added later if retrieval quality requires it.

### ADR-019: Pre-Processing Pipeline is Deterministic
**Status:** Accepted
**Context:** Image preprocessing steps (denoise, deskew, binarize) could be optimized per document type.
**Decision:** Apply a fixed pipeline of all preprocessing steps to every image. Do not use ML to select steps.
**Rationale:** Deterministic preprocessing is simpler, faster, and more reliable. The pipeline is designed to improve OCR on a wide range of document qualities without needing per-document optimization.

### ADR-020: File Storage Abstraction (Local/S3)
**Status:** Accepted
**Context:** Storage backend choice for uploaded files.
**Decision:** Abstract storage behind `FileStorage` interface with `LocalFileStorage` (dev) and `S3FileStorage` (production).
**Rationale:** Enables local development without cloud dependencies while providing production-grade S3 storage. The abstraction also allows future migration to other providers (GCS, Azure Blob) without pipeline changes.

### ADR-021: Quarantine → Scan → Permanent Flow
**Status:** Accepted
**Context:** Security requirements for file uploads.
**Decision:** Files go through a 3-stage flow: quarantine → virus scan → permanent storage. Only files in permanent storage are processed.
**Rationale:** Prevents processing infected files. If virus scan is unavailable, the system logs a warning but proceeds (fail-open for availability). The quarantine directory is cleaned regularly.

### ADR-022: Report Status State Machine with Checkpoints
**Status:** Accepted
**Context:** Long-running pipeline needs to track progress and support resumption.
**Decision:** Each stage saves a checkpoint with intermediate results. The recovery system can resume from the last successful stage.
**Rationale:** Enables retry from point of failure rather than restarting from scratch. Critical for large PDFs where OCR takes minutes. Checkpoints also enable observability into pipeline progress.

### ADR-023: Dead-Letter Queue for Unrecoverable Failures
**Status:** Accepted
**Context:** After exhausting retries, some jobs remain permanently failed.
**Decision:** Move permanently failed jobs to a dead-letter queue with error details. Admin can replay or discard them.
**Rationale:** Prevents infinite retries while preserving failed jobs for debugging and manual recovery. Essential for production reliability.
