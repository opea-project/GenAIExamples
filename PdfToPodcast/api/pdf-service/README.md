# PDF Processing Microservice

Extracts text from PDF documents with advanced OCR support for scanned documents.

## Features

**Multi-Method Extraction**
- pdfplumber for complex layouts
- PyPDF2 fallback
- Tesseract OCR for scanned PDFs

**Intelligent Processing**
- Automatic scanned PDF detection
- Multi-column layout handling
- Table extraction
- Structure analysis (headings, paragraphs)

**Text Cleaning**
- Header/footer removal
- Page number removal
- Whitespace normalization
- Hyphenation fixing
- OCR error correction

**OCR Capabilities**
- Multiple language support
- Adjustable DPI settings
- Confidence scoring
- Image preprocessing

## API Endpoints

### 1. Extract Text (Smart Mode)

**POST** `/extract`

Intelligently extracts text using the best available method.

**Parameters:**
- `file`: PDF file (multipart/form-data)
- `job_id`: Optional tracking ID
- `clean_text`: Apply cleaning (default: true)
- `use_ocr`: Enable OCR fallback (default: true)

**Response:**
```json
{
  "text": "Extracted text content...",
  "metadata": {
    "pages": 10,
    "word_count": 5000,
    "character_count": 30000,
    "has_images": true,
    "method": "pdfplumber"
  },
  "status": "success",
  "method": "pdfplumber"
}
```

### 2. Extract Structure

**POST** `/extract-structure`

Extracts hierarchical document structure.

**Returns:**
```json
{
  "structure": [
    {
      "page": 1,
      "text": "Introduction",
      "type": "heading",
      "font_size": 18
    },
    {
      "page": 1,
      "text": "This document describes...",
      "type": "paragraph",
      "font_size": 12
    }
  ],
  "sections": [
    {
      "heading": "Introduction",
      "content": "..."
    }
  ],
  "status": "success"
}
```

### 3. Force OCR Extraction

**POST** `/extract-with-ocr`

Forces OCR processing for scanned PDFs.

**Parameters:**
- `file`: PDF file
- `language`: OCR language code (default: "eng")
- `dpi`: Image resolution (default: 300)

**Response:**
```json
{
  "text": "OCR extracted text...",
  "metadata": {
    "pages": 10,
    "avg_confidence": 92.5,
    "language": "eng",
    "dpi": 300
  },
  "status": "success",
  "method": "ocr"
}
```

### 4. Health Check

**GET** `/health`

Check service health and capabilities.

**Response:**
```json
{
  "status": "healthy",
  "tesseract_available": true,
  "version": "1.0.0"
}
```

### 5. Supported Languages

**GET** `/languages`

Get list of available OCR languages.

**Response:**
```json
{
  "languages": ["eng", "fra", "deu", "spa"],
  "default": "eng"
}
```

## Prerequisites

- Tesseract OCR (for scanned PDFs)
- Poppler utils
- Python 3.9+

## Installation

### Using Docker

```bash
cd microservices/pdf-service
docker build -t pdf-service .
docker run -p 8001:8001 pdf-service
```

### Manual Installation

1. **Install System Dependencies**

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# macOS
brew install tesseract poppler

# Windows
# Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
# Download Poppler from: https://blog.alivate.com.au/poppler-windows/
```

2. **Install Python Dependencies**

```bash
pip install -r requirements.txt
```

3. **Run Service**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Configuration

Create `.env` file:

```env
SERVICE_PORT=8001
MAX_FILE_SIZE=10485760
TESSERACT_CMD=/usr/bin/tesseract
OCR_LANGUAGE=eng
OCR_DPI=300
ENABLE_TEXT_CLEANING=true
ENABLE_OCR_FALLBACK=true
```

## Usage Examples

### Python

```python
import requests

# Extract text
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8001/extract",
        files={"file": f},
        data={"clean_text": True, "use_ocr": True}
    )

result = response.json()
print(f"Extracted {result['metadata']['word_count']} words")
print(result['text'][:500])
```

### cURL

```bash
# Smart extraction
curl -X POST http://localhost:8001/extract \
  -F "file=@document.pdf" \
  -F "clean_text=true" \
  -F "use_ocr=true"

# Force OCR
curl -X POST http://localhost:8001/extract-with-ocr \
  -F "file=@scanned.pdf" \
  -F "language=eng" \
  -F "dpi=300"
```

## Testing

Test with sample PDF:
```bash
curl -X POST http://localhost:8001/extract \
  -F "file=@sample.pdf"
```

Check service health:
```bash
curl http://localhost:8001/health
```

## Troubleshooting

### Tesseract Not Found

**Error**: `pytesseract.pytesseract.TesseractNotFoundError`

**Solution**:
```bash
# Linux
sudo apt-get install tesseract-ocr

# Set path in .env
TESSERACT_CMD=/usr/bin/tesseract
```

### Poor OCR Quality

**Solutions**:
- Increase DPI: `dpi=600`
- Ensure good scan quality

### Slow Processing

**Solutions**:
- Reduce DPI for OCR
- Disable text cleaning if not needed

## API Documentation

View interactive API docs at `http://localhost:8001/docs`
