from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.core.pdf_extractor import PDFExtractor
from app.core.text_cleaner import TextCleaner
from app.core.ocr_handler import OCRHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize processors
pdf_extractor = PDFExtractor()
text_cleaner = TextCleaner()
ocr_handler = OCRHandler()

class ExtractionResponse(BaseModel):
    text: str
    metadata: dict
    status: str
    method: str

class HealthResponse(BaseModel):
    status: str
    tesseract_available: bool
    version: str

@router.post("/extract", response_model=ExtractionResponse)
async def extract_text(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form(None),
    clean_text: bool = Form(True),
    use_ocr: bool = Form(True)
):
    """
    Extract text from PDF file

    - **file**: PDF file to process
    - **job_id**: Optional job ID for tracking
    - **clean_text**: Apply text cleaning (default: True)
    - **use_ocr**: Use OCR for scanned PDFs (default: True)

    Returns extracted text with metadata
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # Read file content
        content = await file.read()
        logger.info(f"Processing PDF: {file.filename} ({len(content)} bytes)")

        # Extract text using standard methods
        result = pdf_extractor.extract(content)

        # Check if PDF is scanned and needs OCR
        if use_ocr and (not result["text"].strip() or len(result["text"]) < 100):
            logger.info("Low text content detected, checking if scanned...")

            is_scanned = pdf_extractor.check_if_scanned(content)

            if is_scanned and ocr_handler.is_tesseract_available():
                logger.info("PDF appears to be scanned, using OCR...")
                ocr_result = ocr_handler.extract_text_from_pdf(content)

                if ocr_result["text"].strip():
                    result = ocr_result
                    logger.info("OCR extraction successful")

        # Clean text if requested
        if clean_text and result["text"]:
            logger.info("Cleaning extracted text...")
            cleaned_text = text_cleaner.clean(result["text"])

            # Get text statistics
            stats = text_cleaner.get_statistics(cleaned_text)
            result["metadata"].update(stats)

            result["text"] = cleaned_text

        # Add job_id to result
        if job_id:
            result["metadata"]["job_id"] = job_id

        logger.info(
            f"Extraction complete: {result['metadata'].get('word_count', 0)} words, "
            f"method: {result['method']}"
        )

        return ExtractionResponse(
            text=result["text"],
            metadata=result["metadata"],
            status="success",
            method=result["method"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )

@router.post("/extract-structure")
async def extract_structure(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form(None)
):
    """
    Extract structured content from PDF (headings, paragraphs, etc.)

    Returns hierarchical document structure
    """
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        content = await file.read()
        logger.info(f"Extracting structure from: {file.filename}")

        # Extract structure
        structure = pdf_extractor.extract_page_structure(content)

        # Extract text and clean it
        result = pdf_extractor.extract(content)
        cleaned_text = text_cleaner.clean(result["text"])

        # Extract sections
        sections = text_cleaner.extract_sections(cleaned_text)

        return {
            "job_id": job_id,
            "filename": file.filename,
            "structure": structure,
            "sections": sections,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting structure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting structure: {str(e)}"
        )

@router.post("/extract-with-ocr")
async def extract_with_ocr(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    dpi: int = Form(300)
):
    """
    Force OCR extraction (for scanned PDFs)

    - **file**: PDF file
    - **language**: OCR language code (default: eng)
    - **dpi**: Image resolution (default: 300)

    Returns OCR-extracted text
    """
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        if not ocr_handler.is_tesseract_available():
            raise HTTPException(
                status_code=503,
                detail="Tesseract OCR is not available on this server"
            )

        content = await file.read()
        logger.info(f"Performing OCR on: {file.filename}")

        # Extract with OCR
        result = ocr_handler.extract_text_from_pdf(
            content,
            language=language,
            dpi=dpi
        )

        # Clean text
        if result["text"]:
            result["text"] = text_cleaner.clean(result["text"])
            stats = text_cleaner.get_statistics(result["text"])
            result["metadata"].update(stats)

        return {
            "text": result["text"],
            "metadata": result["metadata"],
            "status": "success" if result["text"] else "failed",
            "method": result["method"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OCR extraction failed: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and capabilities"""
    tesseract_available = ocr_handler.is_tesseract_available()

    return HealthResponse(
        status="healthy",
        tesseract_available=tesseract_available,
        version="1.0.0"
    )

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported OCR languages"""
    try:
        languages = ocr_handler.get_supported_languages()
        return {
            "languages": languages,
            "default": "eng"
        }
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}")
        return {
            "languages": ["eng"],
            "default": "eng",
            "error": str(e)
        }
