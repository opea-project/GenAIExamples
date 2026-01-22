"""
API Client for Keycloak authentication and API calls
"""

import logging
import requests
import httpx
from typing import Optional
import config

logger = logging.getLogger(__name__)


class APIClient:
    """
    Client for handling Keycloak authentication and API calls
    """

    def __init__(self):
        self.base_url = config.BASE_URL
        self.token = None
        self.http_client = None
        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate and obtain access token from Keycloak
        """
        token_url = f"{self.base_url}/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": config.KEYCLOAK_CLIENT_ID,
            "client_secret": config.KEYCLOAK_CLIENT_SECRET,
        }

        try:
            response = requests.post(token_url, data=payload, verify=False)

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                logger.info(f"✓ Access token obtained: {self.token[:20]}..." if self.token else "Failed to get token")

                # Create httpx client with SSL verification disabled
                self.http_client = httpx.Client(verify=False)

            else:
                logger.error(f"Error obtaining token: {response.status_code} - {response.text}")
                raise Exception(f"Authentication failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            raise

    def get_inference_client(self):
        """
        Get OpenAI-style client for code generation inference
        Uses CodeLlama-34b-instruct endpoint
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.token,
            base_url=f"{self.base_url}/{config.INFERENCE_MODEL_ENDPOINT}/v1",
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
