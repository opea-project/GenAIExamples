import httpx
import logging
from openai import OpenAI
import config

logger = logging.getLogger(__name__)


class APIClient:
    """
    Client for handling API calls with token-based authentication
    """

    def __init__(self):
        self.base_url = config.INFERENCE_API_ENDPOINT
        self.token = config.INFERENCE_API_TOKEN
        self.http_client = httpx.Client(verify=False)
        logger.info(f"✓ API Client initialized with endpoint: {self.base_url}")

    def get_inference_client(self):
        """
        Get OpenAI-style client for inference/completions
        Uses configured inference model
        """
        return OpenAI(
            api_key=self.token,
            base_url=f"{self.base_url}/v1",
            http_client=self.http_client
        )

    def __del__(self):
        """
        Cleanup: close httpx client
        """
        if self.http_client:
            self.http_client.close()


# Global instance
api_client = None

def get_api_client():
    """Get or create global API client instance"""
    global api_client
    if api_client is None:
        api_client = APIClient()
    return api_client
