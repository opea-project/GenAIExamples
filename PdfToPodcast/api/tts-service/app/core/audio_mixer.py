from pydub import AudioSegment
from pydub.effects import normalize
from pathlib import Path
import logging
from typing import List, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB

logger = logging.getLogger(__name__)

class AudioMixer:
    """Mix and process audio segments"""

    def __init__(self):
        self.silence_duration = 500  # milliseconds between speakers

    def create_silence(self, duration_ms: int) -> AudioSegment:
        """Create silent audio segment"""
        return AudioSegment.silent(duration=duration_ms)

    def load_audio(self, file_path: Path) -> AudioSegment:
        """Load audio file"""
        try:
            audio = AudioSegment.from_mp3(str(file_path))
            logger.info(f"Loaded audio: {file_path} ({len(audio)}ms)")
            return audio
        except Exception as e:
            logger.error(f"Failed to load audio {file_path}: {str(e)}")
            raise

    def mix_segments(
        self,
        segment_paths: List[Path],
        output_path: Path,
        add_silence: bool = True
    ) -> Path:
        """
        Mix audio segments sequentially

        Args:
            segment_paths: List of audio file paths
            output_path: Output file path
            add_silence: Add silence between segments

        Returns:
            Path to mixed audio file
        """
        try:
            logger.info(f"Mixing {len(segment_paths)} segments")

            # Load first segment
            mixed = self.load_audio(segment_paths[0])

            # Add remaining segments
            for i, path in enumerate(segment_paths[1:], 1):
                if add_silence:
                    mixed += self.create_silence(self.silence_duration)

                segment = self.load_audio(path)
                mixed += segment

                if i % 10 == 0:
                    logger.info(f"Mixed {i}/{len(segment_paths)-1} segments")

            logger.info(f"Total duration: {len(mixed)}ms ({len(mixed)/1000/60:.1f} min)")

            # Export
            self._export_audio(mixed, output_path)

            return output_path

        except Exception as e:
            logger.error(f"Mixing failed: {str(e)}")
            raise

    def normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """Normalize audio levels"""
        try:
            normalized = normalize(audio, headroom=0.1)
            logger.info("Audio normalized")
            return normalized
        except Exception as e:
            logger.error(f"Normalization failed: {str(e)}")
            return audio

    def adjust_speed(self, audio: AudioSegment, speed: float) -> AudioSegment:
        """Adjust playback speed"""
        if speed == 1.0:
            return audio

        try:
            # Change speed by changing frame rate
            sound_with_altered_frame_rate = audio._spawn(
                audio.raw_data,
                overrides={"frame_rate": int(audio.frame_rate * speed)}
            )
            # Convert back to original frame rate
            return sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
        except Exception as e:
            logger.error(f"Speed adjustment failed: {str(e)}")
            return audio

    def _export_audio(
        self,
        audio: AudioSegment,
        output_path: Path,
        format: str = "mp3",
        bitrate: str = "192k"
    ):
        """Export audio with settings"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Normalize before export
            audio = self.normalize_audio(audio)

            # Export
            audio.export(
                str(output_path),
                format=format,
                bitrate=bitrate,
                parameters=["-q:a", "2"]  # High quality
            )

            logger.info(f"Exported audio to {output_path}")

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise

    def add_metadata(
        self,
        file_path: Path,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None
    ):
        """Add ID3 metadata to MP3 file"""
        try:
            audio = MP3(str(file_path), ID3=ID3)

            # Add ID3 tag if doesn't exist
            try:
                audio.add_tags()
            except:
                pass

            if title:
                audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            if artist:
                audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
            if album:
                audio.tags["TALB"] = TALB(encoding=3, text=album)

            audio.save()
            logger.info(f"Added metadata to {file_path}")

        except Exception as e:
            logger.error(f"Metadata addition failed: {str(e)}")

    def get_audio_duration(self, file_path: Path) -> float:
        """Get audio duration in seconds"""
        try:
            audio = self.load_audio(file_path)
            return len(audio) / 1000.0
        except Exception as e:
            logger.error(f"Duration calculation failed: {str(e)}")
            return 0.0

    def trim_silence(
        self,
        audio: AudioSegment,
        silence_thresh: int = -50,
        chunk_size: int = 10
    ) -> AudioSegment:
        """Trim leading and trailing silence"""
        try:
            # Detect non-silent parts
            non_silent_ranges = self._detect_nonsilent(
                audio,
                min_silence_len=chunk_size,
                silence_thresh=silence_thresh
            )

            if not non_silent_ranges:
                return audio

            # Get start and end of non-silent audio
            start = non_silent_ranges[0][0]
            end = non_silent_ranges[-1][1]

            return audio[start:end]

        except Exception as e:
            logger.error(f"Silence trimming failed: {str(e)}")
            return audio

    def _detect_nonsilent(
        self,
        audio: AudioSegment,
        min_silence_len: int = 1000,
        silence_thresh: int = -16,
        seek_step: int = 1
    ) -> List[tuple]:
        """Detect non-silent chunks"""
        # Implementation using pydub's silence detection
        from pydub.silence import detect_nonsilent

        return detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            seek_step=seek_step
        )
