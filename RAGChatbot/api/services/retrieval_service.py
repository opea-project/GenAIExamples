"""
Retrieval service
Handles query processing and retrieval chain operations
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import LLMResult, Generation
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from typing import List, Optional, Any
import config

logger = logging.getLogger(__name__)


class CustomLLM(LLM):
    """
    Custom LLM class that uses the Llama-3.1-8B-Instruct endpoint
    """
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "custom_llm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """Call the LLM on the given prompt."""
        from .api_client import get_api_client
        api_client = get_api_client()
        return api_client.complete(prompt, max_tokens=kwargs.get('max_tokens', 150), temperature=kwargs.get('temperature', 0))


class CustomChatModel(BaseChatModel):
    """
    Custom Chat Model that uses the Llama-3.1-8B-Instruct endpoint
    """
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "custom_chat"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate response from messages."""
        from .api_client import get_api_client
        api_client = get_api_client()
        
        # Convert messages to a prompt string
        # Build the prompt from all messages
        prompt_parts = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
        
        # Join all parts and add assistant prompt suffix
        full_prompt = "\n\n".join(prompt_parts)
        if not full_prompt.endswith("Assistant:"):
            full_prompt += "\n\nAssistant:"
        
        logger.info(f"Sending prompt to LLM (length: {len(full_prompt)} chars)")
        
        # Use the complete method which directly sends the prompt
        # This calls: Llama-3.1-8B-Instruct/v1/completions with prompt
        response_text = api_client.complete(
            full_prompt,
            max_tokens=kwargs.get('max_tokens', 150),
            temperature=kwargs.get('temperature', 0)
        )
        
        generations = [Generation(text=response_text)]
        return LLMResult(generations=[generations])


def get_llm(api_key: str) -> BaseChatModel:
    """
    Get LLM instance (ChatOpenAI or CustomChatModel based on config)

    Args:
        api_key: API key

    Returns:
        LLM instance
    """
    # Check if using custom inference endpoint
    if hasattr(config, 'INFERENCE_API_TOKEN') and config.INFERENCE_API_TOKEN:
        return CustomChatModel()
    else:
        # Fallback to OpenAI ChatOpenAI
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=api_key
        )


def build_retrieval_chain(vectorstore: FAISS, api_key: str):
    """
    Build retrieval chain with LLM (ChatOpenAI or CustomChatModel)
    
    Args:
        vectorstore: FAISS vectorstore instance
        api_key: API key
        
    Returns:
        Configured retrieval chain
        
    Raises:
        Exception: If chain building fails
    """
    try:
        retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
        llm = get_llm(api_key)
        combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
        retrieval_chain = create_retrieval_chain(
            vectorstore.as_retriever(search_kwargs={"k": 4}),
            combine_docs_chain
        )
        return retrieval_chain
    except Exception as e:
        logger.error(f"Error building retrieval chain: {str(e)}")
        raise


def query_documents(query: str, vectorstore: FAISS, api_key: str) -> dict:
    """
    Query the documents using RAG with custom embedding and inference
    
    Simple workflow:
    1. Create embedding for the query
    2. Search for similar documents in the vectorstore
    3. Format the retrieved context
    4. Summarize using Llama inference endpoint
    
    Args:
        query: User's question
        vectorstore: FAISS vectorstore instance
        api_key: API key
        
    Returns:
        Dictionary with answer and query
        
    Raises:
        Exception: If query processing fails
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Step 1: Create embedding for the query
        logger.info("Creating query embedding...")
        from .api_client import get_api_client
        api_client = get_api_client()
        
        query_embedding = api_client.embed_text(query)
        logger.info(f"Query embedding created (dimension: {len(query_embedding)})")
        
        # Step 2: Search for similar documents (similarity search)
        logger.info("Searching for similar documents...")
        similar_docs = vectorstore.similarity_search_by_vector(query_embedding, k=4)
        logger.info(f"Found {len(similar_docs)} similar documents")
        
        if not similar_docs:
            return {
                "answer": "I couldn't find any relevant documents to answer your question.",
                "query": query
            }
        
        # Step 3: Format the retrieved context
        context_parts = []
        for i, doc in enumerate(similar_docs):
            context_parts.append(f"Document {i+1}:\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        logger.info(f"Context length: {len(context)} characters")
        
        # Step 4: Create prompt for summarization using Llama
        prompt = f"""Based on the following documents, provide a comprehensive summary that addresses the question.

Documents:
{context}

Question: {query}

Summary:"""
        
        logger.info(f"Calling Llama inference with prompt length: {len(prompt)}")
        
        # Call Llama inference endpoint for summarization
        answer = api_client.complete(
            prompt=prompt,
            max_tokens=200,
            temperature=0
        )
        
        answer = answer.strip()
        
        if not answer:
            answer = "I couldn't find a relevant answer in the documents."
        
        logger.info("✓ Query completed successfully")
        
        return {
            "answer": answer,
            "query": query
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise

