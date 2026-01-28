"""
API Client for inference API calls
"""

import logging
import httpx
from typing import Optional
import config

logger = logging.getLogger(__name__)


class APIClient:
    """
    Client for handling inference API calls
    """

    def __init__(self):
        self.endpoint = config.INFERENCE_API_ENDPOINT
        self.token = config.INFERENCE_API_TOKEN
        self.http_client = httpx.Client(verify=False) if self.token else None

    def get_inference_client(self):
        """
        Get OpenAI-style client for code generation inference
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.token,
            base_url=f"{self.endpoint}/v1",
            http_client=self.http_client
        )

    def translate_code(self, source_code: str, source_lang: str, target_lang: str) -> str:
        """
        Translate code from one language to another using CodeLlama-34b-instruct

        Args:
            source_code: Code to translate
            source_lang: Source programming language
            target_lang: Target programming language

        Returns:
            Translated code
        """
        try:
            client = self.get_inference_client()

            # Create prompt for code translation
            prompt = f"""Translate the following {source_lang} code to {target_lang}.
Only output the translated code without any explanations or markdown formatting.

{source_lang} code:
```
{source_code}
```

{target_lang} code:
```"""

            logger.info(f"Translating code from {source_lang} to {target_lang}")

            # Use completions endpoint for CodeLlama
            response = client.completions.create(
                model=config.INFERENCE_MODEL_NAME,
                prompt=prompt,
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE,
                stop=["```"]  # Stop at closing code block
            )

            # Handle response structure
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'text'):
                    translated_code = choice.text.strip()
                    logger.info(f"Successfully translated code ({len(translated_code)} characters)")
                    return translated_code
                else:
                    logger.error(f"Unexpected response structure: {type(choice)}, {choice}")
                    return ""
            else:
                logger.error(f"Unexpected response: {type(response)}, {response}")
                return ""
        except Exception as e:
            logger.error(f"Error translating code: {str(e)}", exc_info=True)
            raise

    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated
        """
        return self.token is not None

    def __del__(self):
        """
        Cleanup: close httpx client
        """
        if self.http_client:
            self.http_client.close()


# Global API client instance
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """
    Get or create the global API client instance

    Returns:
        APIClient instance
    """
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
