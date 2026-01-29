"""
API Client for authentication and API calls
Similar to simple-client/main.py implementation
"""

import logging
import requests
import httpx
from typing import Optional
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
    
    def get_embedding_client(self):
        """
        Get OpenAI-style client for embeddings
        Uses bge-base-en-v1.5 model
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.token,
            base_url=f"{self.base_url}/v1",
            http_client=self.http_client
        )
    
    def get_inference_client(self):
        """
        Get OpenAI-style client for inference/completions
        Uses Llama-3.1-8B-Instruct model
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.token,
            base_url=f"{self.base_url}/v1",
            http_client=self.http_client
        )
    
    def embed_text(self, text: str) -> list:
        """
        Get embedding for text
        Uses the bge-base-en-v1.5 embedding model
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            client = self.get_embedding_client()
            # Call the embeddings endpoint
            response = client.embeddings.create(
                model=config.EMBEDDING_MODEL_NAME,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def embed_texts(self, texts: list) -> list:
        """
        Get embeddings for multiple texts
        Batches requests to avoid exceeding API limits (max batch size: 32)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            BATCH_SIZE = 32  # Maximum allowed batch size
            all_embeddings = []
            client = self.get_embedding_client()
            
            # Process in batches of 32
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i:i + BATCH_SIZE]
                logger.info(f"Processing embedding batch {i//BATCH_SIZE + 1}/{(len(texts) + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} texts)")
                
                response = client.embeddings.create(
                    model=config.EMBEDDING_MODEL_NAME,
                    input=batch
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def complete(self, prompt: str, max_tokens: int = 50, temperature: float = 0) -> str:
        """
        Get completion from the inference model
        Uses Llama-3.1-8B-Instruct for inference
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated text
        """
        try:
            client = self.get_inference_client()
            logger.info(f"Calling inference client with model: {config.INFERENCE_MODEL_NAME}")
            response = client.completions.create(
                model=config.INFERENCE_MODEL_NAME,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Handle response structure
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, 'text'):
                    return choice.text
                else:
                    logger.error(f"Unexpected choice structure: {type(choice)}, {choice}")
                    return str(choice)
            else:
                logger.error(f"Unexpected response: {type(response)}, {response}")
                return ""
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}", exc_info=True)
            raise
    
    def chat_complete(self, messages: list, max_tokens: int = 150, temperature: float = 0) -> str:
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
            # (since Llama models use completions, not chat.completions)
            prompt = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'system':
                    prompt += f"System: {content}\n\n"
                elif role == 'user':
                    prompt += f"User: {content}\n\n"
                elif role == 'assistant':
                    prompt += f"Assistant: {content}\n\n"
            prompt += "Assistant:"
            
            logger.info(f"Calling inference with prompt length: {len(prompt)}")
            
            response = client.completions.create(
                model=config.INFERENCE_MODEL_NAME,
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

