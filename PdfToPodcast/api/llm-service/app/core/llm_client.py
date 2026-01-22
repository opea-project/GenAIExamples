import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import json
from typing import Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with OpenAI API or Custom API
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        default_model: str = "gpt-4-turbo-preview"
    ):
        """
        Initialize LLM client

        Args:
            openai_api_key: OpenAI API key
            default_model: Default model to use
        """
        self.openai_api_key = openai_api_key
        self.default_model = default_model
        self.custom_api_client = None
        self.using_custom_api = False
        self.openai_client = None

        # Check if custom API is configured
        if settings.BASE_URL and settings.KEYCLOAK_CLIENT_SECRET:
            logger.info("Initializing LLM Client with custom API")
            logger.info(f"Custom API Base URL: {settings.BASE_URL}")
            logger.info(f"Model: {settings.INFERENCE_MODEL_NAME}")

            try:
                from app.services.api_client import get_api_client
                self.custom_api_client = get_api_client()
                if self.custom_api_client.is_authenticated():
                    self.using_custom_api = True
                    self.default_model = settings.INFERENCE_MODEL_NAME
                    logger.info("Custom API client initialized successfully")
                else:
                    logger.error("Custom API authentication failed")
            except Exception as e:
                logger.error(f"Failed to initialize custom API client: {str(e)}")
                self.using_custom_api = False
        else:
            logger.info("Initializing LLM Client with OpenAI")
            # Initialize OpenAI client
            if openai_api_key:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
            else:
                self.openai_client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_with_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate text using OpenAI or Custom API

        Args:
            system_prompt: System message
            user_prompt: User message
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        # Use custom API if configured
        if self.using_custom_api and self.custom_api_client:
            try:
                model = model or self.default_model
                logger.info(f"Generating with custom API model: {model}")

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
                logger.error(f"Custom API generation failed: {str(e)}")
                raise

        # Use OpenAI
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            model = model or self.default_model
            logger.info(f"Generating with OpenAI model: {model}")

            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if "gpt-4" in model else None
            )

            content = response.choices[0].message.content
            logger.info(f"Generated {len(content)} characters")

            return content

        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: str = "openai",
        **kwargs
    ) -> str:
        """
        Generate text using OpenAI

        Args:
            system_prompt: System message
            user_prompt: User message
            provider: "openai" (for compatibility)
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        return await self.generate_with_openai(
            system_prompt,
            user_prompt,
            **kwargs
        )

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """
        Estimate token count for text

        Args:
            text: Text to count
            model: Model for tokenization

        Returns:
            Estimated token count
        """
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))

        except Exception as e:
            logger.error(f"Token counting failed: {str(e)}")
            # Rough estimate: ~4 characters per token
            return len(text) // 4

    def is_available(self, provider: str = "openai") -> bool:
        """
        Check if LLM client is available

        Args:
            provider: Provider to check

        Returns:
            True if available
        """
        if self.using_custom_api:
            return self.custom_api_client is not None and self.custom_api_client.is_authenticated()
        return self.openai_client is not None
