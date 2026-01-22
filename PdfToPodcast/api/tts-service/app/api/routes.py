from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path
import logging
import os
import uuid

from app.core.audio_generator import AudioGenerator
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize audio generator
OUTPUT_DIR = Path(settings.OUTPUT_DIR)
audio_generator = AudioGenerator(
    openai_api_key=settings.OPENAI_API_KEY or "",
    output_dir=OUTPUT_DIR,
    tts_model=settings.TTS_MODEL
)

# Job storage (in production, use Redis/database)
jobs = {}

class GenerateAudioRequest(BaseModel):
    script: List[Dict[str, str]] = Field(..., description="Podcast script")
    host_voice: str = Field(default="alloy", description="Host voice ID")
    guest_voice: str = Field(default="nova", description="Guest voice ID")
    job_id: Optional[str] = Field(default=None, description="Optional job ID")

class AudioStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    audio_url: Optional[str] = None
    metadata: Optional[Dict] = None

class VoiceInfo(BaseModel):
    id: str
    name: str
    description: str
    gender: str
    suitable_for: List[str]

class VoicesResponse(BaseModel):
    voices: List[Dict]
    default_host: str
    default_guest: str

class HealthResponse(BaseModel):
    status: str
    tts_available: bool
    version: str

async def generation_task(
    job_id: str,
    script: List[Dict[str, str]],
    host_voice: str,
    guest_voice: str
):
    """Background task for audio generation"""
    try:
        # Update job status
        jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting audio generation..."
        }

        # Progress callback
        async def progress_callback(job_id, progress, message):
            jobs[job_id] = {
                "status": "processing",
                "progress": progress,
                "message": message
            }

        # Generate podcast
        result = await audio_generator.generate_podcast(
            script=script,
            host_voice=host_voice,
            guest_voice=guest_voice,
            job_id=job_id,
            progress_callback=progress_callback
        )

        # Update job with results
        jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Audio generation complete!",
            "audio_url": result["audio_url"],
            "metadata": result["metadata"]
        }

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        jobs[job_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Error: {str(e)}"
        }

@router.post("/generate-audio")
async def generate_audio(
    request: GenerateAudioRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate podcast audio from script

    - **script**: List of dialogue objects with speaker and text
    - **host_voice**: Voice ID for host (default: alloy)
    - **guest_voice**: Voice ID for guest (default: nova)
    - **job_id**: Optional job ID for tracking

    Returns job ID for status tracking
    """
    try:
        # Validate script
        if not request.script or len(request.script) < 2:
            raise HTTPException(
                status_code=400,
                detail="Script must have at least 2 dialogue turns"
            )

        # Generate job ID
        job_id = request.job_id or str(uuid.uuid4())

        # Initialize job
        jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Job queued for processing"
        }

        # Start background task
        background_tasks.add_task(
            generation_task,
            job_id,
            request.script,
            request.host_voice,
            request.guest_voice
        )

        logger.info(f"Started job {job_id}")

        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Audio generation started"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start audio generation: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=AudioStatusResponse)
async def get_status(job_id: str):
    """
    Get audio generation status

    Returns current status and progress
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    job = jobs[job_id]

    return AudioStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        audio_url=job.get("audio_url"),
        metadata=job.get("metadata")
    )

@router.get("/download/{job_id}")
async def download_audio(job_id: str):
    """
    Download generated podcast audio

    Returns audio file for streaming/download
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )

    # Get audio file path
    audio_path = OUTPUT_DIR / job_id / f"podcast_{job_id}.mp3"

    if not audio_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )

    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=f"podcast_{job_id}.mp3"
    )

@router.get("/voices", response_model=VoicesResponse)
async def get_voices():
    """
    Get list of available voices

    Returns all available voices with metadata
    """
    try:
        voices_data = audio_generator.get_available_voices()
        return VoicesResponse(**voices_data)

    except Exception as e:
        logger.error(f"Failed to get voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve voices"
        )

@router.get("/voice-sample/{voice_id}")
async def get_voice_sample(voice_id: str):
    """
    Get voice sample audio

    Returns sample audio for the specified voice
    """
    try:
        sample_path = await audio_generator.generate_voice_sample(voice_id)

        return FileResponse(
            path=str(sample_path),
            media_type="audio/mpeg",
            filename=f"sample_{voice_id}.mp3"
        )

    except Exception as e:
        logger.error(f"Failed to generate sample: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate voice sample: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health"""
    tts_available = audio_generator.tts_client.is_available()

    return HealthResponse(
        status="healthy" if tts_available else "degraded",
        tts_available=tts_available,
        version="1.0.0"
    )

@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete job and associated files"""
    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    # Delete job directory
    job_dir = OUTPUT_DIR / job_id
    if job_dir.exists():
        import shutil
        shutil.rmtree(job_dir)

    # Remove from jobs dict
    del jobs[job_id]

    return {"message": f"Job {job_id} deleted"}
