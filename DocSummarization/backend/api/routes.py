"""
API Routes for Doc-Sum Application
Handles all HTTP endpoints
"""

from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import os
import logging
import json

from services import pdf_service, llm_service
import config
from models import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - checks service configuration"""
    return HealthResponse(
        status="healthy",
        service=config.APP_TITLE,
        version=config.APP_VERSION,
        llm_provider="Enterprise Inference (Token-based)"
    )


@router.post("/v1/docsum")
async def summarize_document(
    type: str = Form(...),
    messages: str = Form(""),
    max_tokens: int = Form(1024),
    language: str = Form("en"),
    summary_type: str = Form("auto"),
    stream: str = Form("false"),
    files: Optional[UploadFile] = File(None)
):
    """
    Summarize text or PDF document content

    Args:
        type: Input type (text, pdf)
        messages: Text content (for type='text')
        max_tokens: Maximum summary length
        language: Language code
        summary_type: Type of summary
        stream: Enable streaming response
        files: Uploaded file (for pdf documents)

    Returns:
        Summary response with text
    """
    try:
        stream_bool = stream.lower() == "true"

        logger.info(f"Request received - type: {type}, has_file: {files is not None}, messages_len: {len(messages)}")

        # ========== Text Input ==========
        if type == "text" and messages.strip():
            logger.info("Processing text input")
            summary = llm_service.summarize(
                text=messages,
                max_tokens=max_tokens,
                stream=stream_bool
            )

            if stream_bool:
                return StreamingResponse(
                    _format_stream(summary),
                    media_type="text/event-stream"
                )
            else:
                return {
                    "text": summary,
                    "summary": summary,
                    "word_count": len(summary.split()),
                    "char_count": len(summary)
                }

        # ========== File Upload (Documents) ==========
        if files:
            # Save file temporarily
            temp_path = f"/tmp/{files.filename}"
            filename_lower = files.filename.lower()
            logger.info(f"Saving uploaded file: {files.filename}, type={type}")

            with open(temp_path, "wb") as buffer:
                content = await files.read()
                buffer.write(content)

            try:
                # ===== Document Processing (PDF/DOC/DOCX/TXT) =====
                # Check file extension to determine how to extract text
                if filename_lower.endswith(('.pdf', '.docx', '.doc')):
                    file_type = "PDF" if filename_lower.endswith('.pdf') else "DOCX"
                    logger.info(f"Extracting text from {file_type} file")
                    text_content = pdf_service.extract_text(temp_path)
                    os.remove(temp_path)

                    if not text_content.strip():
                        raise HTTPException(status_code=400, detail=f"No text found in {file_type}")

                    logger.info(f"Extracted {len(text_content)} characters, generating summary")
                    summary = llm_service.summarize(
                        text=text_content,
                        max_tokens=max_tokens,
                        stream=stream_bool
                    )

                    if stream_bool:
                        return StreamingResponse(
                            _format_stream(summary),
                            media_type="text/event-stream"
                        )
                    else:
                        return {
                            "text": summary,
                            "summary": summary,
                            "word_count": len(summary.split()),
                            "char_count": len(summary)
                        }

                elif filename_lower.endswith('.txt'):
                    logger.info("Reading text from TXT file")
                    with open(temp_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                    os.remove(temp_path)

                    if not text_content.strip():
                        raise HTTPException(status_code=400, detail="No text found in file")

                    logger.info(f"Read {len(text_content)} characters, generating summary")
                    summary = llm_service.summarize(
                        text=text_content,
                        max_tokens=max_tokens,
                        stream=stream_bool
                    )

                    if stream_bool:
                        return StreamingResponse(
                            _format_stream(summary),
                            media_type="text/event-stream"
                        )
                    else:
                        return {
                            "text": summary,
                            "summary": summary,
                            "word_count": len(summary.split()),
                            "char_count": len(summary)
                        }

                else:
                    logger.error(f"Unsupported file type: {files.filename}")
                    os.remove(temp_path)
                    raise HTTPException(status_code=400, detail=f"Unsupported file type. Please upload PDF, DOCX, or TXT files.")

            except Exception as e:
                # Clean up file on error
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise

        # ========== Invalid Request ==========
        raise HTTPException(
            status_code=400,
            detail="Either text message or file is required"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization error: {str(e)}")


def _format_stream(generator):
    """
    Format streaming response for SSE

    Args:
        generator: Text chunk generator

    Yields:
        Formatted SSE data chunks
    """
    try:
        for chunk in generator:
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
