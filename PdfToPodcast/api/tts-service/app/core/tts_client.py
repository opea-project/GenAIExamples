import openai
from pathlib import Path
import logging
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class TTSClient:
    """
    Client for OpenAI Text-to-Speech API
    """

    def __init__(self, api_key: str, model: str = "tts-1-hd"):
        """
        Initialize TTS client

        Args:
            api_key: OpenAI API key
            model: TTS model (tts-1 or tts-1-hd)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    async def generate_speech(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        Generate speech audio from text

        Args:
            text: Text to convert
            voice: Voice ID (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            output_path: Optional path to save audio

        Returns:
            Audio bytes
        """
        try:
            logger.info(f"Generating speech: voice={voice}, length={len(text)} chars")

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.audio.speech.create(
                    model=self.model,
                    voice=voice,
                    input=text,
                    speed=speed
                )
            )

            # Get audio content
            audio_bytes = response.content

            # Save if path provided
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                logger.info(f"Saved audio to {output_path}")

            logger.info(f"Generated {len(audio_bytes)} bytes of audio")
            return audio_bytes

        except Exception as e:
            logger.error(f"Speech generation failed: {str(e)}")
            raise

    async def generate_speech_batch(
        self,
        texts: list[str],
        voices: list[str],
        output_dir: Path
    ) -> list[Path]:
        """
        Generate speech for multiple texts in parallel

        Args:
            texts: List of texts
            voices: List of voice IDs
            output_dir: Directory to save audio files

        Returns:
            List of output paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        output_paths = []

        for i, (text, voice) in enumerate(zip(texts, voices)):
            output_path = output_dir / f"segment_{i:03d}.mp3"
            output_paths.append(output_path)

            task = self.generate_speech(
                text=text,
                voice=voice,
                output_path=output_path
            )
            tasks.append(task)

        # Run in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def bounded_task(task):
            async with semaphore:
                return await task

        await asyncio.gather(*[bounded_task(task) for task in tasks])

        logger.info(f"Generated {len(output_paths)} audio segments")
        return output_paths

    def get_available_voices(self) -> list[str]:
        """Get list of available voices"""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def is_available(self) -> bool:
        """Check if TTS service is available"""
        try:
            # Simple check - could be improved with actual API call
            return self.client is not None
        except:
            return False
