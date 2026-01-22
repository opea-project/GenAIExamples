"""
API Client for authentication and API calls
Similar to RAG chatbot implementation
"""

import logging
import requests
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """
    Client for handling authentication and API calls
    """

    def __init__(self):
        self.base_url = settings.BASE_URL
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
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        }

        try:
            response = requests.post(token_url, data=payload, verify=False)

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                logger.info(f"✓ Access token obtained: {self.token[:20]}..." if self.token else "Failed to get token")

                # Create httpx client with SSL verification disabled (like -k in curl)
                self.http_client = httpx.Client(verify=False)

            else:
                logger.error(f"Error obtaining token: {response.status_code} - {response.text}")
                raise Exception(f"Authentication failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            raise

    def get_inference_client(self):
        """
        Get OpenAI-style client for inference/completions
        Uses Llama-3.1-8B-Instruct endpoint
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.token,
            base_url=f"{self.base_url}/{settings.INFERENCE_MODEL_ENDPOINT}/v1",
            http_client=self.http_client
        )

    def chat_complete(self, messages: list, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """
        Get chat completion from the inference model

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Generated text
        """
        try:
            client = self.get_inference_client()

            # Convert messages to a prompt for the completions endpoint
            prompt = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'system':
                    prompt += f"{content}\n\n"
                elif role == 'user':
                    prompt += f"User: {content}\n\n"
                elif role == 'assistant':
                    prompt += f"Assistant: {content}\n\n"
            prompt += "Assistant:"

            logger.info(f"Calling inference with prompt length: {len(prompt)}")

            # Use completions.create (not chat.completions) as per curl example
            response = client.completions.create(
                model=settings.INFERENCE_MODEL_NAME,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Handle response structure
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'text'):
                    return choice.text
                elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return choice.message.content
                else:
                    logger.error(f"Unexpected response structure: {type(choice)}, {choice}")
                    return str(choice)
            else:
                logger.error(f"Unexpected response: {type(response)}, {response}")
                return ""
        except Exception as e:
            logger.error(f"Error generating chat completion: {str(e)}", exc_info=True)
            raise

    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.token is not None and self.http_client is not None

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
