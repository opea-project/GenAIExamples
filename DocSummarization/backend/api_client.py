import requests
import httpx
import logging
from openai import OpenAI
import config

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.token = None
        self.http_client = None

        if self.base_url and config.KEYCLOAK_CLIENT_SECRET:
            self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate and obtain access token from Keycloak"""
        try:
            token_url = f"{self.base_url}/token"
            logger.info(f"Authenticating with Keycloak at {token_url}")

            payload = {
                "grant_type": "client_credentials",
                "client_id": config.KEYCLOAK_CLIENT_ID,
                "client_secret": config.KEYCLOAK_CLIENT_SECRET,
            }

            response = requests.post(token_url, data=payload, verify=False)

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.http_client = httpx.Client(verify=False)
                logger.info("Authentication successful")
            else:
                raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

    def get_inference_client(self):
        """Get OpenAI-style client for inference/completions"""
        if not self.token or not self.http_client:
            raise ValueError("API client not authenticated")

        return OpenAI(
            api_key=self.token,
            base_url=f"{self.base_url}/{config.INFERENCE_MODEL_ENDPOINT}/v1",
            http_client=self.http_client
        )

    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.token is not None and self.http_client is not None


# Global instance
api_client = None

def get_api_client():
    """Get or create global API client instance"""
    global api_client
    if api_client is None:
        api_client = APIClient()
    return api_client
