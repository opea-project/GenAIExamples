import logging
from typing import Dict, Optional
from app.prompts.templates import (
    get_system_prompt,
    get_user_prompt,
    get_content_length_prompt
)

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Build prompts for podcast script generation
    """

    def __init__(self):
        self.system_prompt = get_system_prompt()

    def build_generation_prompt(
        self,
        content: str,
        tone: str = "conversational",
        max_length: int = 2000,
        host_name: str = "Host",
        guest_name: str = "Guest"
    ) -> Dict[str, str]:
        """
        Build prompts for script generation

        Args:
            content: Source content
            tone: Conversation tone
            max_length: Target word count
            host_name: Host name
            guest_name: Guest name

        Returns:
            Dict with system and user prompts
        """
        # Calculate target number of dialogue turns
        # Rough estimate: 50-100 words per turn
        target_turns = max(10, min(30, max_length // 75))

        # Build user prompt
        user_prompt = get_user_prompt(
            content=content,
            tone=tone,
            target_turns=target_turns
        )

        # Add length-specific guidance
        content_length = len(content)
        length_prompt = get_content_length_prompt(content_length, target_turns)

        if length_prompt:
            user_prompt += f"\n\n{length_prompt}"

        # Add names if custom
        if host_name != "Host" or guest_name != "Guest":
            user_prompt += f"\n\nUse these names:\n- Host: {host_name}\n- Guest: {guest_name}"

        logger.info(f"Built prompt for {content_length} chars, targeting {target_turns} turns")

        return {
            "system": self.system_prompt,
            "user": user_prompt
        }

    def build_refinement_prompt(self, script: list) -> Dict[str, str]:
        """
        Build prompts for script refinement

        Args:
            script: Current script

        Returns:
            Dict with system and user prompts
        """
        from app.prompts.templates import SCRIPT_REFINEMENT_PROMPT

        user_prompt = SCRIPT_REFINEMENT_PROMPT.format(
            current_script=script
        )

        return {
            "system": self.system_prompt,
            "user": user_prompt
        }
