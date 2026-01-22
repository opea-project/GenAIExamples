"""
Keycloak Authentication Client for DocuGen
Handles token acquisition and management for enterprise inference endpoints
"""

import logging
import requests
import httpx
from typing import Optional
from langchain_openai import ChatOpenAI
from config import settings

logger = logging.getLogger(__name__)


class KeycloakClient:
    """
    Client for handling Keycloak authentication and creating LLM clients

    Features:
    - Persistent token storage
    - Automatic token acquisition via client_credentials grant
    - SSL verification bypass for internal endpoints
    - httpx client management for API calls
    """

    def __init__(self):
        """Initialize Keycloak client and authenticate"""
        self.base_url = settings.BASE_URL
        self.token = None
        self.http_client = None

        # Authenticate immediately
        self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate with Keycloak and obtain access token

        Token endpoint: {BASE_URL}/token
        Grant type: client_credentials

        Raises:
            Exception: If authentication fails
        """
        if not self.base_url:
            raise ValueError("BASE_URL is required for Keycloak authentication")

        if not settings.KEYCLOAK_CLIENT_SECRET:
            raise ValueError("KEYCLOAK_CLIENT_SECRET is required for Keycloak authentication")

        token_url = f"{self.base_url}/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.KEYCLOAK_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
        }

        try:
            logger.info(f"Authenticating with Keycloak at: {token_url}")

            # Disable SSL verification for internal endpoints (like -k in curl)
            response = requests.post(token_url, data=payload, verify=False)

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                if self.token:
                    logger.info(f"✓ Access token obtained: {self.token[:20]}...")
                else:
                    logger.error("❌ No access token in response")
                    raise Exception("Access token not found in response")

                # Create httpx client with SSL verification disabled
                self.http_client = httpx.Client(verify=False)
                logger.info("✓ httpx client initialized")

            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                raise Exception(f"Authentication failed: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Error during Keycloak authentication: {str(e)}")
            raise

    def get_llm_client(self, model_name: str, temperature: float = 0.7, max_tokens: int = 2000) -> ChatOpenAI:
        """
        Get LangChain ChatOpenAI client configured with Keycloak token

        Args:
            model_name: Model name to use (e.g., "Qwen/Qwen2.5-32B-Instruct", "Llama-3.1-8B-Instruct")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            ChatOpenAI instance configured for Keycloak endpoint

        Raises:
            ValueError: If not authenticated
        """
        if not self.is_authenticated():
            raise ValueError("Keycloak client is not authenticated")

        logger.info(f"Creating LLM client for model: {model_name}")

        # Create ChatOpenAI with Keycloak token as API key
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=self.token,
            openai_api_base=f"{self.base_url}/v1",
            max_tokens=max_tokens,
            http_client=self.http_client
        )

    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated

        Returns:
            True if token and http_client are available
        """
        return self.token is not None and self.http_client is not None

    def __del__(self):
        """Cleanup: Close httpx client on deletion"""
        if self.http_client:
            try:
                self.http_client.close()
                logger.debug("httpx client closed")
            except Exception as e:
                logger.warning(f"Error closing httpx client: {e}")


# Global Keycloak client instance (singleton pattern)
_keycloak_client: Optional[KeycloakClient] = None


def get_keycloak_client() -> KeycloakClient:
    """
    Get or create the global Keycloak client instance

    Uses singleton pattern to reuse token across multiple LLM requests

    Returns:
        KeycloakClient instance

    Raises:
        Exception: If authentication fails
    """
    global _keycloak_client
    if _keycloak_client is None:
        logger.info("Initializing global Keycloak client")
        _keycloak_client = KeycloakClient()
    return _keycloak_client
