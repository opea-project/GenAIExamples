import logging
from typing import Dict, List, Optional
from app.core.llm_client import LLMClient
from app.core.prompt_builder import PromptBuilder
from app.core.script_formatter import ScriptFormatter

logger = logging.getLogger(__name__)

class DialogueGenerator:
    """
    Main orchestrator for podcast dialogue generation
    """

    def __init__(self):
        """
        Initialize dialogue generator
        """
        self.llm_client = LLMClient()
        self.prompt_builder = PromptBuilder()
        self.formatter = ScriptFormatter()

    async def generate_script(
        self,
        text: str,
        host_name: str = "Host",
        guest_name: str = "Guest",
        tone: str = "conversational",
        max_length: int = 2000,
        provider: str = "inference",
        **kwargs
    ) -> Dict:
        """
        Generate podcast script from text

        Args:
            text: Source content
            host_name: Host name
            guest_name: Guest name
            tone: Conversation tone
            max_length: Target word count
            provider: LLM provider to use
            **kwargs: Additional parameters

        Returns:
            Dict with script and metadata
        """
        try:
            logger.info(f"Generating script for {len(text)} chars of content")

            # Validate input
            if not text or len(text.strip()) < 50:
                raise ValueError("Content too short for script generation")

            # Build prompts
            prompts = self.prompt_builder.build_generation_prompt(
                content=text,
                tone=tone,
                max_length=max_length,
                host_name=host_name,
                guest_name=guest_name
            )

            # Generate with LLM
            response = await self.llm_client.generate(
                system_prompt=prompts["system"],
                user_prompt=prompts["user"],
                provider=provider,
                temperature=0.7,
                max_tokens=4000
            )

            # Parse and validate response
            script = self.formatter.parse_llm_response(response)

            if not self.formatter.validate_script(script):
                raise ValueError("Generated script failed validation")

            # Post-process script
            script = self.formatter.merge_short_turns(script)
            script = self.formatter.truncate_script(script, max_turns=50)

            # Format for TTS
            tts_script = self.formatter.format_for_tts(script)

            # Calculate metadata
            metadata = self.formatter.calculate_metadata(tts_script)
            metadata["tone"] = tone
            metadata["host_name"] = host_name
            metadata["guest_name"] = guest_name
            metadata["source_length"] = len(text)

            logger.info(
                f"Generated script: {metadata['total_turns']} turns, "
                f"{metadata['estimated_duration_minutes']} min"
            )

            return {
                "script": tts_script,
                "metadata": metadata,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}")
            raise

    async def refine_script(
        self,
        script: List[Dict[str, str]],
        provider: str = "inference"
    ) -> Dict:
        """
        Refine an existing script

        Args:
            script: Current script
            provider: LLM provider

        Returns:
            Dict with refined script and metadata
        """
        try:
            logger.info(f"Refining script with {len(script)} turns")

            # Build refinement prompts
            prompts = self.prompt_builder.build_refinement_prompt(script)

            # Generate refinement
            response = await self.llm_client.generate(
                system_prompt=prompts["system"],
                user_prompt=prompts["user"],
                provider=provider,
                temperature=0.5,  # Lower temperature for refinement
                max_tokens=4000
            )

            # Parse response
            refined_script = self.formatter.parse_llm_response(response)

            if not self.formatter.validate_script(refined_script):
                logger.warning("Refined script invalid, returning original")
                return {
                    "script": script,
                    "metadata": self.formatter.calculate_metadata(script),
                    "status": "unchanged"
                }

            # Format and calculate metadata
            tts_script = self.formatter.format_for_tts(refined_script)
            metadata = self.formatter.calculate_metadata(tts_script)

            logger.info("Script refinement successful")

            return {
                "script": tts_script,
                "metadata": metadata,
                "status": "refined"
            }

        except Exception as e:
            logger.error(f"Script refinement failed: {str(e)}")
            # Return original script on failure
            return {
                "script": script,
                "metadata": self.formatter.calculate_metadata(script),
                "status": "error",
                "error": str(e)
            }

    def validate_content_length(self, text: str) -> Dict:
        """
        Validate if content is suitable for podcast generation

        Args:
            text: Content to validate

        Returns:
            Dict with validation results
        """
        word_count = len(text.split())
        char_count = len(text)

        # Check token count
        token_count = self.llm_client.count_tokens(text)

        issues = []
        recommendations = []

        # Too short
        if word_count < 100:
            issues.append("Content is very short")
            recommendations.append("Add more context or background information")

        # Too long
        if token_count > 8000:
            issues.append("Content may be too long for single request")
            recommendations.append("Consider breaking into multiple sections")

        # Very technical
        technical_indicators = ["algorithm", "theorem", "equation", "formula"]
        if any(word in text.lower() for word in technical_indicators):
            recommendations.append("Consider using 'educational' tone for technical content")

        return {
            "valid": len(issues) == 0,
            "word_count": word_count,
            "char_count": char_count,
            "token_count": token_count,
            "issues": issues,
            "recommendations": recommendations
        }
