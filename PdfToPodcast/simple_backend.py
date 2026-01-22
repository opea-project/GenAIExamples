"""
Simple Backend Gateway for Testing
Routes requests from frontend to microservices directly
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import logging
import sys
import asyncio
import os

# Suppress Windows asyncio errors
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Backend Gateway")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
PDF_SERVICE = os.getenv("PDF_SERVICE_URL", os.getenv("PDF_SERVICE", "http://localhost:8001"))
LLM_SERVICE = os.getenv("LLM_SERVICE_URL", os.getenv("LLM_SERVICE", "http://localhost:8002"))
TTS_SERVICE = os.getenv("TTS_SERVICE_URL", os.getenv("TTS_SERVICE", "http://localhost:8003"))

class GenerateScriptRequest(BaseModel):
    text: str
    host_name: Optional[str] = "Host"
    guest_name: Optional[str] = "Guest"
    tone: Optional[str] = "conversational"
    max_length: Optional[int] = 500

class GenerateScriptFromJobRequest(BaseModel):
    job_id: str
    host_voice: Optional[str] = "alloy"
    guest_voice: Optional[str] = "echo"

# Simple in-memory storage for job data
job_storage = {}

@app.get("/")
async def root():
    return {
        "service": "Simple Backend Gateway",
        "status": "running",
        "endpoints": {
            "upload": "POST /api/upload",
            "generate_script": "POST /api/generate-script",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "services": {
        "pdf": PDF_SERVICE,
        "llm": LLM_SERVICE,
        "tts": TTS_SERVICE
    }}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and extract text"""
    logger.info(f"Received PDF upload: {file.filename}")

    try:
        # Read file content
        pdf_content = await file.read()
        logger.info(f"PDF size: {len(pdf_content)} bytes")

        # Send to PDF service
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (file.filename, pdf_content, "application/pdf")}
            response = await client.post(f"{PDF_SERVICE}/extract", files=files)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Extracted {len(result.get('text', ''))} characters")

                # Generate a simple job ID from filename
                import time
                job_id = f"{file.filename}_{int(time.time())}"

                # Store the extracted text for later use
                job_storage[job_id] = {
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "filename": file.filename
                }

                return JSONResponse({
                    "status": "success",
                    "job_id": job_id,
                    "text": result.get("text", ""),
                    "metadata": result.get("metadata", {}),
                    "filename": file.filename
                })
            else:
                logger.error(f"PDF service error: {response.text}")
                raise HTTPException(status_code=500, detail="PDF extraction failed")

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-script")
async def generate_script(request: GenerateScriptFromJobRequest):
    """Generate podcast script from job"""
    logger.info(f"Generating script for job: {request.job_id}")

    # Retrieve stored text from job_id
    if request.job_id not in job_storage:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")

    job_data = job_storage[request.job_id]
    text = job_data["text"]

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "text": text,
                "host_name": "Host",
                "guest_name": "Guest",
                "tone": "conversational",
                "max_length": 500
            }

            response = await client.post(
                f"{LLM_SERVICE}/generate-script",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Generated {len(result.get('script', []))} dialogue turns")

                # Store the script in job storage
                job_storage[request.job_id]["script"] = result.get("script", [])
                job_storage[request.job_id]["host_voice"] = request.host_voice
                job_storage[request.job_id]["guest_voice"] = request.guest_voice

                return result
            else:
                logger.error(f"LLM service error: {response.text}")
                raise HTTPException(status_code=500, detail="Script generation failed")

    except Exception as e:
        logger.error(f"Script generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voices")
async def get_voices():
    """Get available TTS voices"""
    # Return default voices (TTS service not implemented yet)
    return {
        "alloy": {"name": "Alloy", "description": "Neutral and balanced", "gender": "neutral"},
        "echo": {"name": "Echo", "description": "Deep and resonant", "gender": "male"},
        "fable": {"name": "Fable", "description": "Expressive and dynamic", "gender": "neutral"},
        "onyx": {"name": "Onyx", "description": "Strong and authoritative", "gender": "male"},
        "nova": {"name": "Nova", "description": "Warm and friendly", "gender": "female"},
        "shimmer": {"name": "Shimmer", "description": "Bright and energetic", "gender": "female"}
    }

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    logger.info(f"Job status requested: {job_id}")

    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job_data = job_storage[job_id]

    # Check if script and audio have been generated
    has_script = "script" in job_data and job_data["script"]
    has_audio = job_data.get("audio_generated", False)
    is_generating_audio = job_data.get("audio_generating", False)

    # If audio is being generated, poll TTS service for status
    if is_generating_audio and not has_audio:
        try:
            tts_job_id = job_data.get("tts_job_id", job_id)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{TTS_SERVICE}/status/{tts_job_id}")

                if response.status_code == 200:
                    tts_status = response.json()
                    logger.info(f"TTS status for {job_id}: {tts_status.get('status')}")

                    # Update job storage with TTS status
                    if tts_status.get("status") == "completed":
                        job_data["audio_generated"] = True
                        job_data["audio_generating"] = False
                        job_data["audio_url"] = f"/api/download/{job_id}"
                        job_data["audio_status"] = "completed"
                        has_audio = True
                        is_generating_audio = False
                    elif tts_status.get("status") == "failed":
                        job_data["audio_generating"] = False
                        job_data["audio_status"] = tts_status.get("message", "Audio generation failed")

        except Exception as e:
            logger.error(f"Error checking TTS status: {str(e)}")

    # Determine status
    if has_audio:
        status = "completed"
        progress = 100
    elif has_script:
        status = "script_generated"
        progress = 75
    else:
        status = "processing"
        progress = 50

    return JSONResponse({
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "script": job_data.get("script"),
        "audio_url": job_data.get("audio_url"),
        "audio_status": job_data.get("audio_status"),
        "metadata": {
            "filename": job_data.get("filename"),
            "host_voice": job_data.get("host_voice"),
            "guest_voice": job_data.get("guest_voice")
        }
    })

@app.post("/api/generate-audio")
async def generate_audio(request: dict):
    """Generate audio from script"""
    job_id = request.get("job_id")
    edited_script = request.get("script")  # Get edited script if provided
    logger.info(f"Audio generation requested for job: {job_id}")

    if not job_id or job_id not in job_storage:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job_data = job_storage[job_id]

    # Check if audio is already generated or being generated
    if job_data.get("audio_generated", False):
        logger.info(f"Audio already generated for job: {job_id}")
        return JSONResponse({
            "status": "success",
            "message": "Audio already generated",
            "job_id": job_id
        })

    if job_data.get("audio_generating", False):
        logger.info(f"Audio generation already in progress for job: {job_id}")
        return JSONResponse({
            "status": "success",
            "message": "Audio generation in progress",
            "job_id": job_id
        })

    # Use edited script if provided, otherwise use stored script
    script_to_use = edited_script if edited_script else job_data.get("script")

    # Check if script exists
    if not script_to_use:
        raise HTTPException(status_code=400, detail="No script available for this job")

    # Update job_data with edited script if provided
    if edited_script:
        job_data["script"] = edited_script
        job_storage[job_id] = job_data
        logger.info(f"Using edited script for job {job_id}: {len(edited_script)} dialogue turns")

    try:
        # Send to TTS service
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "script": script_to_use,
                "host_voice": job_data.get("host_voice", "alloy"),
                "guest_voice": job_data.get("guest_voice", "echo"),
                "job_id": job_id
            }

            logger.info(f"Sending to TTS service: {len(job_data['script'])} dialogue turns")

            response = await client.post(
                f"{TTS_SERVICE}/generate-audio",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"TTS service accepted job: {job_id}")

                # Mark as generating
                job_storage[job_id]["audio_generating"] = True
                job_storage[job_id]["tts_job_id"] = result.get("job_id", job_id)

                return JSONResponse({
                    "status": "success",
                    "message": "Audio generation started",
                    "job_id": job_id
                })
            else:
                logger.error(f"TTS service error: {response.text}")
                # Fallback to mock if TTS service fails
                job_storage[job_id]["audio_generated"] = True
                job_storage[job_id]["audio_url"] = None
                job_storage[job_id]["audio_status"] = "TTS service unavailable"

                return JSONResponse({
                    "status": "success",
                    "message": "Audio generation requires TTS service",
                    "job_id": job_id
                })

    except httpx.ConnectError:
        logger.warning(f"TTS service not available, using fallback")
        # Fallback if TTS service not running
        job_storage[job_id]["audio_generated"] = True
        job_storage[job_id]["audio_url"] = None
        job_storage[job_id]["audio_status"] = "TTS service not available"

        return JSONResponse({
            "status": "success",
            "message": "Audio generation requires TTS service (Python 3.11)",
            "job_id": job_id
        })

    except Exception as e:
        logger.error(f"Audio generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{job_id}")
async def download_audio(job_id: str):
    """Download audio file"""
    logger.info(f"Download requested for job: {job_id}")

    try:
        # Proxy the download request to TTS service
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{TTS_SERVICE}/download/{job_id}")

            if response.status_code == 200:
                from fastapi.responses import StreamingResponse
                import io

                # Stream the audio file back to the client
                audio_content = response.content
                return StreamingResponse(
                    io.BytesIO(audio_content),
                    media_type="audio/mpeg",
                    headers={
                        "Content-Disposition": f'attachment; filename="podcast_{job_id}.mp3"'
                    }
                )
            else:
                logger.error(f"TTS service download error: {response.text}")
                raise HTTPException(status_code=404, detail="Audio file not found")

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice/sample/{voice_id}")
async def get_voice_sample(voice_id: str):
    """Get voice sample audio"""
    logger.info(f"Voice sample requested: {voice_id}")

    # Return URL to the static audio file
    return JSONResponse({
        "voice_id": voice_id,
        "status": "available",
        "audio_url": f"/voice-samples/{voice_id}.mp3"
    })

if __name__ == "__main__":
    import uvicorn
    print("Starting Simple Backend Gateway on http://localhost:8000")
    print("Forwarding to:")
    print(f"  - PDF Service: {PDF_SERVICE}")
    print(f"  - LLM Service: {LLM_SERVICE}")
    print(f"  - TTS Service: {TTS_SERVICE}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
