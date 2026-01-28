from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with inference API
    """

    def __init__(self):
        """
        Initialize LLM client with inference API
        """
        self.custom_api_client = None
        self.default_model = settings.INFERENCE_MODEL_NAME

        if not settings.INFERENCE_API_ENDPOINT or not settings.INFERENCE_API_TOKEN:
            raise ValueError("INFERENCE_API_ENDPOINT and INFERENCE_API_TOKEN are required")

        logger.info("Initializing LLM Client with inference API")
        logger.info(f"Inference API Endpoint: {settings.INFERENCE_API_ENDPOINT}")
        logger.info(f"Model: {settings.INFERENCE_MODEL_NAME}")

        try:
            from app.services.api_client import get_api_client
            self.custom_api_client = get_api_client()
            if not self.custom_api_client.is_authenticated():
                raise ValueError("Inference API authentication failed")
            logger.info("Inference API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize inference API client: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_with_inference(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate text using inference API

        Args:
            system_prompt: System message
            user_prompt: User message
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            model = model or self.default_model
            logger.info(f"Generating with inference API model: {model}")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            content = self.custom_api_client.chat_complete(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            logger.info(f"Generated {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Inference API generation failed: {str(e)}")
            raise

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: str = "inference",
        **kwargs
    ) -> str:
        """
        Generate text using inference API

        Args:
            system_prompt: System message
            user_prompt: User message
            provider: Provider (for compatibility)
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        return await self.generate_with_inference(
            system_prompt,
            user_prompt,
            **kwargs
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """
        Estimate token count for text

        Args:
            text: Text to count
            model: Model for tokenization (unused)

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def is_available(self, provider: str = "inference") -> bool:
        """
        Check if inference API client is available

        Args:
            provider: Provider to check

        Returns:
            True if available
        """
        return self.custom_api_client is not None and self.custom_api_client.is_authenticated()
