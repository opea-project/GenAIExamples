"""
LLM Service for Document Summarization
Uses Enterprise Inference API via token-based authentication
"""

from typing import Iterator, Dict, Any
import logging
import re
import config
from api_client import get_api_client

logger = logging.getLogger(__name__)


def clean_markdown_formatting(text: str) -> str:
    """
    Remove markdown formatting symbols from text

    Args:
        text: Text that may contain markdown formatting

    Returns:
        Clean text without markdown symbols
    """
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove code blocks (```text```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Remove inline code (`text`)
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove headers (# text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Remove bullet points and list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    return text.strip()


class LLMService:
    """
    LLM service for document summarization using enterprise inference
    """

    def __init__(self):
        """Initialize LLM service"""
        self.client = None
        self.model = config.INFERENCE_MODEL_NAME
        self._initialized = False

    def _ensure_initialized(self):
        """Initialize LLM client (lazy initialization)"""
        if self._initialized:
            return

        logger.info("Initializing LLM Service with Enterprise API")
        logger.info(f"Inference Endpoint: {config.INFERENCE_API_ENDPOINT}")
        logger.info(f"Model: {config.INFERENCE_MODEL_NAME}")

        # Get API client instance
        api_client = get_api_client()
        self.client = api_client.get_inference_client()
        self._initialized = True
        logger.info("✓ Enterprise API client initialized successfully")

    def summarize(
        self,
        text: str,
        max_tokens: int = None,
        temperature: float = None,
        stream: bool = False
    ) -> str | Iterator[str]:
        """
        Summarize text using enterprise LLM

        Args:
            text: Text to summarize
            max_tokens: Maximum tokens in summary
            temperature: Generation temperature
            stream: Whether to stream response

        Returns:
            Summary text or iterator of chunks if streaming
        """
        # Ensure client is initialized before making API calls
        self._ensure_initialized()

        max_tokens = max_tokens or config.LLM_MAX_TOKENS
        temperature = temperature or config.LLM_TEMPERATURE

        system_prompt = """You are a professional document summarizer.
Your task is to create clear, concise, and accurate summaries of the provided text.
Focus on the main points and key information while maintaining the original meaning.

IMPORTANT: Provide the summary in plain text format only. Do not use any markdown formatting symbols like **, *, _, or other special characters for formatting. Write in a clean, readable paragraph format."""

        user_prompt = f"""Please provide a comprehensive summary of the following text:

{text}

Summary:"""

        try:
            logger.info(f"Generating summary with {self.model} (stream={stream})")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )

            if stream:
                return self._stream_response(response)
            else:
                summary = response.choices[0].message.content
                # Clean any markdown formatting from the response
                summary = clean_markdown_formatting(summary)
                logger.info(f"Generated summary: {len(summary)} characters")
                return summary

        except Exception as e:
            logger.error(f"LLM summarization error: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")

    def _stream_response(self, response) -> Iterator[str]:
        """Stream LLM response chunks (with markdown cleaning)"""
        accumulated = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                accumulated += chunk.choices[0].delta.content
                # Only yield when we have a complete sentence or paragraph
                if accumulated.endswith(('.', '!', '?', '\n')):
                    cleaned = clean_markdown_formatting(accumulated)
                    yield cleaned
                    accumulated = ""

        # Yield any remaining content
        if accumulated:
            cleaned = clean_markdown_formatting(accumulated)
            yield cleaned

    def health_check(self) -> Dict[str, Any]:
        """
        Check if LLM service is healthy

        Returns:
            Health status dictionary
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Try a simple completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say 'OK'"}],
                max_tokens=10
            )

            return {
                "status": "healthy",
                "provider": "Enterprise Inference (Token-based)",
                "model": self.model,
                "endpoint": config.INFERENCE_API_ENDPOINT
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "provider": "Enterprise Inference (Token-based)",
                "error": str(e)
            }


# Global LLM service instance
llm_service = LLMService()
