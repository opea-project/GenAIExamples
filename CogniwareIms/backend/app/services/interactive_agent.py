# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA Interactive Agent Service Handles conversational AI interactions with context awareness."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .dbqna_service import dbqna_service
from .embedding_service import embedding_service
from .llm_service import llm_service
from .retrieval_service import retrieval_service

logger = logging.getLogger(__name__)


class InteractiveAgent:
    """Interactive conversational agent for inventory management Combines RAG, DBQnA, and chat capabilities."""

    def __init__(self):
        self.conversation_history = {}  # Session-based conversation memory
        self.max_history = 10  # Keep last 10 messages per session

    def _get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        return self.conversation_history[session_id]

    def _add_to_history(self, session_id: str, role: str, content: str):
        """Add message to conversation history."""
        history = self._get_session_history(session_id)
        history.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})

        # Keep only last N messages
        if len(history) > self.max_history * 2:  # *2 for user+assistant pairs
            self.conversation_history[session_id] = history[-(self.max_history * 2) :]

    async def chat(
        self,
        message: str,
        session_id: str,
        user_role: str = "Inventory Manager",
        use_rag: bool = True,
        use_dbqna: bool = True,
    ) -> Dict[str, Any]:
        """Process a chat message with full context awareness.

        Args:
            message: User's message
            session_id: Conversation session ID
            user_role: User's role for context
            use_rag: Use retrieval-augmented generation
            use_dbqna: Use database query for structured data

        Returns:
            Agent response with sources and metadata
        """
        try:
            logger.info(f"Interactive agent processing: {message[:100]}...")

            # Determine if this is a database query
            is_data_query = await self._is_database_query(message)

            context_parts = []
            sources = []

            # Step 1: Retrieve relevant context using RAG
            if use_rag:
                rag_context = await self._get_rag_context(message)
                if rag_context:
                    context_parts.append("Knowledge Base Context:")
                    context_parts.append(rag_context["text"])
                    sources.extend(rag_context.get("sources", []))

            # Step 2: Query database if needed
            if use_dbqna and is_data_query:
                db_result = await dbqna_service.query_inventory(message)
                if db_result.get("success"):
                    context_parts.append("Current Database Information:")
                    context_parts.append(json.dumps(db_result.get("result", {}), indent=2))
                    sources.append({"type": "database", "query": message})

            # Step 3: Get conversation history
            history = self._get_session_history(session_id)

            # Step 4: Build messages for LLM
            messages = self._build_chat_messages(
                user_message=message,
                context="\n\n".join(context_parts) if context_parts else None,
                history=history,
                user_role=user_role,
            )

            # Step 5: Generate response
            response_text = await llm_service.chat_completion(messages=messages, temperature=0.7)

            # Step 6: Update conversation history
            self._add_to_history(session_id, "user", message)
            self._add_to_history(session_id, "assistant", response_text)

            logger.info(f"Generated response for session {session_id}")

            return {
                "success": True,
                "response": response_text,
                "sources": sources,
                "metadata": {
                    "session_id": session_id,
                    "used_rag": use_rag and len(sources) > 0,
                    "used_dbqna": use_dbqna and is_data_query,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Interactive agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request. Please try rephrasing your question.",
            }

    async def _is_database_query(self, message: str) -> bool:
        """Determine if message requires database query."""
        # Keywords that indicate database query
        db_keywords = [
            "how many",
            "show me",
            "list",
            "count",
            "total",
            "inventory",
            "stock",
            "warehouse",
            "allocation",
            "available",
            "in stock",
            "quantity",
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in db_keywords)

    async def _get_rag_context(self, query: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
        """Get relevant context from knowledge base using RAG."""
        try:
            # Generate query embedding
            query_embedding = await embedding_service.embed_text(query)

            # Search vector store
            results = await retrieval_service.search(query_embedding=query_embedding, top_k=top_k)

            if not results:
                return None

            # Combine retrieved documents
            context_texts = []
            sources = []

            for result in results:
                context_texts.append(result.get("text", ""))
                sources.append(
                    {
                        "doc_id": result.get("doc_id"),
                        "score": result.get("score", 0),
                        "metadata": result.get("metadata", {}),
                    }
                )

            return {"text": "\n\n".join(context_texts), "sources": sources}

        except Exception as e:
            logger.error(f"RAG context retrieval error: {e}")
            return None

    def _build_chat_messages(
        self,
        user_message: str,
        context: Optional[str],
        history: List[Dict[str, str]],
        user_role: str,
    ) -> List[Dict[str, str]]:
        """Build message list for LLM including context and history."""

        # System prompt based on user role
        role_prompts = {
            "Consumer": "You are a helpful AI assistant for product research and PC building. Help users find products and make informed decisions.",
            "Inventory Manager": "You are an AI assistant for inventory management. Help with stock queries, warehouse operations, and data analysis. Be precise with numbers and locations.",
            "Super Admin": "You are an AI assistant for system administration. Provide comprehensive insights and administrative support.",
        }

        system_content = role_prompts.get(user_role, "You are a helpful AI assistant.")

        if context:
            system_content += f"\n\nRelevant Context:\n{context}"

        messages = [{"role": "system", "content": system_content}]

        # Add conversation history (last 5 exchanges)
        recent_history = history[-(min(len(history), 10)) :]
        for msg in recent_history:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def get_conversation_summary(self, session_id: str) -> str:
        """Generate summary of conversation."""
        history = self._get_session_history(session_id)

        if not history:
            return "No conversation history"

        # Build conversation text
        conv_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

        summary = await llm_service.summarize_text(conv_text, max_length=100)
        return summary

    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Cleared session: {session_id}")

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.conversation_history.keys())


# Global instance
interactive_agent = InteractiveAgent()
