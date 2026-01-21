"""
LLM Service - Handles LLM initialization based on authentication mode
Supports GenAI Gateway and Keycloak authentication
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from config import settings, AuthMode

logger = logging.getLogger(__name__)


def get_llm(model_name: Optional[str] = None, temperature: float = 0.7) -> ChatOpenAI:
    """
    Get LLM instance based on authentication mode

    Args:
        model_name: Override model name (required - specify which agent model to use)
        temperature: Temperature for generation

    Returns:
        ChatOpenAI instance configured for the auth mode
    """
    if model_name is None:
        raise ValueError("model_name is required. Use settings.CODE_EXPLORER_MODEL, settings.PLANNER_MODEL, etc.")

    model_name = model_name

    if settings.AUTH_MODE == AuthMode.GENAI_GATEWAY:
        # GenAI Gateway
        if not settings.GENAI_GATEWAY_URL or not settings.GENAI_GATEWAY_API_KEY:
            raise ValueError("GENAI_GATEWAY_URL and API_KEY are required for GenAI Gateway mode")

        logger.info(f"Initializing GenAI Gateway LLM with model: {model_name}")

        # Create httpx client with SSL verification disabled for self-signed certs
        import httpx
        http_client = httpx.Client(verify=False)
        async_http_client = httpx.AsyncClient(verify=False)

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=settings.GENAI_GATEWAY_API_KEY,
            openai_api_base=settings.GENAI_GATEWAY_URL,
            max_tokens=settings.AGENT_MAX_TOKENS,
            http_client=http_client,
            http_async_client=async_http_client
        )

    elif settings.AUTH_MODE == AuthMode.KEYCLOAK:
        # Keycloak Enterprise Inference (Robust implementation with persistent token)
        if not all([settings.BASE_URL, settings.KEYCLOAK_CLIENT_ID, settings.KEYCLOAK_CLIENT_SECRET]):
            raise ValueError("Keycloak configuration incomplete")

        logger.info(f"Initializing Keycloak LLM with model: {model_name}")

        # Use dedicated Keycloak client with token management
        from services.keycloak_client import get_keycloak_client

        try:
            keycloak_client = get_keycloak_client()
            return keycloak_client.get_llm_client(
                model_name=model_name,
                temperature=temperature,
                max_tokens=settings.AGENT_MAX_TOKENS
            )
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak LLM client: {e}")
            raise ValueError(f"Keycloak authentication failed: {str(e)}")

    else:
        raise ValueError(f"Unknown authentication mode: {settings.AUTH_MODE}")
