import json
from pathlib import Path
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class VoiceManager:
    """Manage voice configurations and mappings"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize voice manager

        Args:
            config_path: Path to voices.json config file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "voices.json"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load voice configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load voice config: {str(e)}")
            # Return default config
            return {
                "openai_voices": {
                    "alloy": {"name": "Alloy"},
                    "nova": {"name": "Nova"}
                },
                "default_voices": {"host": "alloy", "guest": "nova"}
            }

    def get_voice_info(self, voice_id: str) -> Dict:
        """Get voice information"""
        voices = self.config.get("openai_voices", {})
        return voices.get(voice_id, {"name": voice_id})

    def get_default_voice(self, role: str = "host") -> str:
        """Get default voice for role"""
        defaults = self.config.get("default_voices", {})
        return defaults.get(role, "alloy")

    def get_all_voices(self) -> Dict:
        """Get all available voices"""
        return self.config.get("openai_voices", {})

    def validate_voice(self, voice_id: str) -> bool:
        """Check if voice ID is valid"""
        voices = self.config.get("openai_voices", {})
        return voice_id in voices

    def get_audio_settings(self) -> Dict:
        """Get audio generation settings"""
        return self.config.get("audio_settings", {
            "format": "mp3",
            "sample_rate": 24000,
            "model": "tts-1-hd",
            "speed": 1.0
        })
