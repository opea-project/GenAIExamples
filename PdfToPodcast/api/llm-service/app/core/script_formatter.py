import json
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ScriptFormatter:
    """
    Format and validate podcast scripts
    """

    def parse_llm_response(self, response: str) -> List[Dict[str, str]]:
        """
        Parse LLM response into structured script

        Args:
            response: Raw LLM response

        Returns:
            List of dialogue objects
        """
        try:
            # Remove markdown code blocks if present
            cleaned = self._remove_markdown(response)
            logger.info(f"Cleaned response (first 200 chars): {cleaned[:200]}")

            # Try to parse as JSON
            script = json.loads(cleaned)
            logger.info(f"Parsed JSON type: {type(script)}")

            # Handle wrapped response (e.g., {"dialogue": [...]})
            if isinstance(script, dict):
                if "dialogue" in script:
                    script = script["dialogue"]
                    logger.info("Extracted dialogue from wrapped response")
                elif "script" in script:
                    script = script["script"]
                    logger.info("Extracted script from wrapped response")
                else:
                    logger.error(f"Expected list or wrapped object, got dict with keys: {list(script.keys())}")
                    raise ValueError("Script must be a list or contain 'dialogue'/'script' key")

            # Validate format
            if not isinstance(script, list):
                logger.error(f"Expected list, got {type(script)}: {str(script)[:200]}")
                raise ValueError("Script must be a list")

            # Validate each dialogue
            validated = []
            for item in script:
                if isinstance(item, dict) and "speaker" in item and "text" in item:
                    validated.append({
                        "speaker": str(item["speaker"]).lower(),
                        "text": str(item["text"]).strip()
                    })

            if not validated:
                raise ValueError("No valid dialogues found")

            logger.info(f"Parsed {len(validated)} dialogue turns")
            return validated

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            # Try to extract dialogue from text
            return self._extract_from_text(response)

        except Exception as e:
            logger.error(f"Script parsing failed: {str(e)}")
            raise

    def _remove_markdown(self, text: str) -> str:
        """Remove markdown code blocks and reasoning tags"""
        # Remove DeepSeek R1 thinking process (everything before </think>)
        if '</think>' in text:
            text = text.split('</think>', 1)[1]
            logger.info("Removed DeepSeek R1 thinking process")

        # Remove <think> tags if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # Remove ```json or ``` blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        return text.strip()

    def _extract_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract dialogue from plain text format

        Handles formats like:
        Host: Welcome to the show!
        Guest: Thanks for having me!
        """
        dialogues = []

        # Split by lines
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Match "Speaker: Text" format
            match = re.match(r'^(Host|Guest|host|guest):(.+)$', line, re.IGNORECASE)
            if match:
                speaker = match.group(1).lower()
                text = match.group(2).strip()

                dialogues.append({
                    "speaker": speaker,
                    "text": text
                })

        if dialogues:
            logger.info(f"Extracted {len(dialogues)} dialogues from text")
            return dialogues

        raise ValueError("Could not parse script format")

    def validate_script(self, script: List[Dict[str, str]]) -> bool:
        """
        Validate script format

        Args:
            script: Script to validate

        Returns:
            True if valid
        """
        if not isinstance(script, list):
            return False

        if len(script) < 2:
            logger.warning("Script too short (< 2 turns)")
            return False

        for item in script:
            if not isinstance(item, dict):
                return False
            if "speaker" not in item or "text" not in item:
                return False
            if item["speaker"] not in ["host", "guest"]:
                logger.warning(f"Invalid speaker: {item['speaker']}")
                return False
            if not item["text"].strip():
                return False

        return True

    def format_for_tts(self, script: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format script for TTS processing

        Args:
            script: Raw script

        Returns:
            TTS-ready script
        """
        formatted = []

        for item in script:
            text = item["text"]

            # Clean up text for TTS
            text = self._prepare_for_speech(text)

            formatted.append({
                "speaker": item["speaker"],
                "text": text
            })

        return formatted

    def _prepare_for_speech(self, text: str) -> str:
        """
        Prepare text for natural speech synthesis

        Args:
            text: Raw text

        Returns:
            Speech-ready text
        """
        # Remove excessive punctuation
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

        return text.strip()

    def calculate_metadata(self, script: List[Dict[str, str]]) -> Dict:
        """
        Calculate script metadata

        Args:
            script: Script

        Returns:
            Metadata dict
        """
        total_words = sum(len(item["text"].split()) for item in script)
        total_chars = sum(len(item["text"]) for item in script)

        # Estimate duration (rough: 150 words per minute)
        estimated_duration_minutes = total_words / 150

        # Count turns per speaker
        host_turns = sum(1 for item in script if item["speaker"] == "host")
        guest_turns = sum(1 for item in script if item["speaker"] == "guest")

        return {
            "total_turns": len(script),
            "host_turns": host_turns,
            "guest_turns": guest_turns,
            "total_words": total_words,
            "total_characters": total_chars,
            "estimated_duration_minutes": round(estimated_duration_minutes, 1),
            "avg_words_per_turn": round(total_words / len(script), 1) if script else 0
        }

    def truncate_script(self, script: List[Dict[str, str]], max_turns: int) -> List[Dict[str, str]]:
        """
        Truncate script to maximum number of turns

        Args:
            script: Script to truncate
            max_turns: Maximum turns

        Returns:
            Truncated script
        """
        if len(script) <= max_turns:
            return script

        logger.info(f"Truncating script from {len(script)} to {max_turns} turns")
        return script[:max_turns]

    def merge_short_turns(self, script: List[Dict[str, str]], min_words: int = 5) -> List[Dict[str, str]]:
        """
        Merge very short turns with adjacent turns from same speaker

        Args:
            script: Script to process
            min_words: Minimum words per turn

        Returns:
            Merged script
        """
        if not script:
            return script

        merged = []
        current = script[0].copy()

        for item in script[1:]:
            current_words = len(current["text"].split())

            # If current turn is short and same speaker, merge
            if current_words < min_words and item["speaker"] == current["speaker"]:
                current["text"] += " " + item["text"]
            else:
                merged.append(current)
                current = item.copy()

        # Add last turn
        merged.append(current)

        if len(merged) < len(script):
            logger.info(f"Merged {len(script) - len(merged)} short turns")

        return merged
