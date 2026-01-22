from pathlib import Path
import logging
import uuid
from typing import Dict, List, Optional
import asyncio

from app.core.tts_client import TTSClient
from app.core.audio_mixer import AudioMixer
from app.core.voice_manager import VoiceManager

logger = logging.getLogger(__name__)

class AudioGenerator:
    """
    Main orchestrator for podcast audio generation
    """

    def __init__(
        self,
        openai_api_key: str,
        output_dir: Path,
        tts_model: str = "tts-1-hd"
    ):
        """
        Initialize audio generator

        Args:
            openai_api_key: OpenAI API key
            output_dir: Directory for output files
            tts_model: TTS model to use
        """
        self.tts_client = TTSClient(openai_api_key, model=tts_model)
        self.audio_mixer = AudioMixer()
        self.voice_manager = VoiceManager()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_podcast(
        self,
        script: List[Dict[str, str]],
        host_voice: str = "alloy",
        guest_voice: str = "nova",
        job_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Generate complete podcast audio from script

        Args:
            script: List of dialogue objects
            host_voice: Voice ID for host
            guest_voice: Voice ID for guest
            job_id: Optional job ID
            progress_callback: Optional progress callback

        Returns:
            Dict with audio_url and metadata
        """
        try:
            if not job_id:
                job_id = str(uuid.uuid4())

            logger.info(f"Generating podcast for job {job_id}")
            logger.info(f"Script: {len(script)} turns, host={host_voice}, guest={guest_voice}")

            # Validate voices
            if not self.voice_manager.validate_voice(host_voice):
                logger.warning(f"Invalid host voice {host_voice}, using default")
                host_voice = self.voice_manager.get_default_voice("host")

            if not self.voice_manager.validate_voice(guest_voice):
                logger.warning(f"Invalid guest voice {guest_voice}, using default")
                guest_voice = self.voice_manager.get_default_voice("guest")

            # Create job directory
            job_dir = self.output_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            segments_dir = job_dir / "segments"
            segments_dir.mkdir(exist_ok=True)

            # Update progress
            if progress_callback:
                await progress_callback(job_id, 10, "Generating audio segments...")

            # Prepare texts and voices
            texts = [item["text"] for item in script]
            voices = [
                host_voice if item["speaker"].lower() == "host" else guest_voice
                for item in script
            ]

            # Generate segments in parallel
            segment_paths = await self._generate_segments(
                texts=texts,
                voices=voices,
                output_dir=segments_dir,
                progress_callback=lambda prog: (
                    progress_callback(job_id, 10 + int(prog * 0.7), "Generating segments...")
                    if progress_callback else None
                )
            )

            # Update progress
            if progress_callback:
                await progress_callback(job_id, 80, "Mixing audio segments...")

            # Mix segments
            output_path = job_dir / f"podcast_{job_id}.mp3"
            mixed_path = self.audio_mixer.mix_segments(
                segment_paths=segment_paths,
                output_path=output_path,
                add_silence=True
            )

            # Add metadata
            self.audio_mixer.add_metadata(
                file_path=mixed_path,
                title=f"Podcast {job_id}",
                artist="PDF to Podcast",
                album="Generated Podcasts"
            )

            # Calculate duration
            duration = self.audio_mixer.get_audio_duration(mixed_path)

            # Update progress
            if progress_callback:
                await progress_callback(job_id, 100, "Podcast generation complete!")

            logger.info(f"Podcast generated: {mixed_path} ({duration:.1f}s)")

            return {
                "job_id": job_id,
                "audio_url": f"/static/{job_id}/podcast_{job_id}.mp3",
                "local_path": str(mixed_path),
                "metadata": {
                    "duration_seconds": round(duration, 2),
                    "duration_minutes": round(duration / 60, 2),
                    "total_segments": len(script),
                    "host_voice": host_voice,
                    "guest_voice": guest_voice,
                    "file_size_mb": round(mixed_path.stat().st_size / 1024 / 1024, 2)
                },
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Podcast generation failed: {str(e)}")
            raise

    async def _generate_segments(
        self,
        texts: List[str],
        voices: List[str],
        output_dir: Path,
        progress_callback: Optional[callable] = None
    ) -> List[Path]:
        """
        Generate all audio segments

        Args:
            texts: List of texts
            voices: List of voice IDs
            output_dir: Output directory
            progress_callback: Optional progress callback

        Returns:
            List of segment paths
        """
        segment_paths = []
        total = len(texts)

        # Create tasks for parallel generation
        tasks = []
        for i, (text, voice) in enumerate(zip(texts, voices)):
            output_path = output_dir / f"segment_{i:03d}.mp3"
            segment_paths.append(output_path)

            task = self.tts_client.generate_speech(
                text=text,
                voice=voice,
                output_path=output_path
            )
            tasks.append((i, task))

        # Process with progress tracking
        completed = 0
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

        async def process_with_progress(index, task):
            nonlocal completed
            async with semaphore:
                await task
                completed += 1
                if progress_callback and completed % 5 == 0:
                    progress = (completed / total) * 100
                    await progress_callback(progress)

        await asyncio.gather(*[process_with_progress(i, task) for i, task in tasks])

        logger.info(f"Generated {len(segment_paths)} segments")
        return segment_paths

    def get_available_voices(self) -> Dict:
        """Get all available voices with metadata"""
        voices = self.voice_manager.get_all_voices()

        return {
            "voices": [
                {
                    "id": voice_id,
                    **voice_info
                }
                for voice_id, voice_info in voices.items()
            ],
            "default_host": self.voice_manager.get_default_voice("host"),
            "default_guest": self.voice_manager.get_default_voice("guest")
        }

    async def generate_voice_sample(
        self,
        voice_id: str,
        sample_text: str = "Hello! This is a sample of my voice for the podcast."
    ) -> Path:
        """
        Generate voice sample

        Args:
            voice_id: Voice ID
            sample_text: Text to speak

        Returns:
            Path to sample audio
        """
        sample_dir = self.output_dir / "samples"
        sample_dir.mkdir(parents=True, exist_ok=True)

        output_path = sample_dir / f"sample_{voice_id}.mp3"

        await self.tts_client.generate_speech(
            text=sample_text,
            voice=voice_id,
            output_path=output_path
        )

        return output_path
