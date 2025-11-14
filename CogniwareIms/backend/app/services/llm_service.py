# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA LLM Service Integration Handles text generation, chat, and intelligent responses."""

import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LLMService:
    """Integration with OPEA LLM microservice for text generation."""

    def __init__(self):
        self.base_url = os.getenv("OPEA_LLM_URL", "http://llm-service:9000")
        self.model_id = os.getenv("LLM_MODEL_ID", "Intel/neural-chat-7b-v3-3")
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.max_tokens = int(os.getenv("MAX_TOTAL_TOKENS", "2048"))

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate chat completion using OPEA LLM service.

        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens or self.max_tokens,
                }

                response = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
                response.raise_for_status()
                result = response.json()

                # Extract generated text
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                elif "text" in result:
                    return result["text"]
                else:
                    raise ValueError("Invalid LLM response format")

        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise

    async def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """Simple text generation from prompt."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat_completion(messages, temperature)

    async def query_with_context(self, question: str, context: str, system_prompt: Optional[str] = None) -> str:
        """Query LLM with context (RAG pattern)

        Args:
            question: User's question
            context: Retrieved context from knowledge base
            system_prompt: Optional system instructions
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Combine context and question
        prompt = f"""Context information:
{context}

Question: {question}

Based on the context above, provide a detailed and accurate answer:"""

        messages.append({"role": "user", "content": prompt})

        return await self.chat_completion(messages, temperature=0.3)  # Lower temp for factual responses

    async def generate_sql_query(self, natural_language_query: str, schema: Dict[str, Any]) -> str:
        """Generate SQL query from natural language (for DBQnA)

        Args:
            natural_language_query: User's question in natural language
            schema: Database schema information
        """
        schema_str = json.dumps(schema, indent=2)

        system_prompt = f"""You are an expert SQL generator. Given a database schema and a natural language question, generate a valid SQL query.

Database Schema:
{schema_str}

Rules:
1. Generate only the SQL query, no explanations
2. Use proper JOIN syntax when needed
3. Include WHERE clauses for filtering
4. Use aggregate functions (COUNT, SUM, AVG) when appropriate
5. Return valid PostgreSQL syntax"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate SQL for: {natural_language_query}"},
        ]

        sql = await self.chat_completion(messages, temperature=0.1)

        # Clean up the response
        sql = sql.strip()
        if sql.startswith("```sql"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        elif sql.startswith("```"):
            sql = sql.replace("```", "").strip()

        return sql

    async def summarize_text(self, text: str, max_length: int = 150) -> str:
        """Summarize long text using OPEA DocSummarization pattern."""
        prompt = f"""Summarize the following text in {max_length} words or less. Focus on key points and important details:

Text:
{text}

Summary:"""

        return await self.generate_text(prompt, temperature=0.3)

    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text Useful for inventory data extraction."""
        prompt = f"""Extract all product names, SKUs, quantities, and locations from the following text. Return as JSON list.

Text: {text}

Extract and return JSON format:
[{{"entity_type": "product", "value": "...", "context": "..."}}, ...]"""

        response = await self.generate_text(prompt, temperature=0.1)

        try:
            # Try to parse JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].strip()
            else:
                json_str = response

            entities = json.loads(json_str)
            return entities if isinstance(entities, list) else []
        except Exception as e:
            logger.error(f"Entity extraction parsing error: {e}")
            return []

    async def generate_inventory_insights(self, data: Dict[str, Any]) -> str:
        """Generate insights from inventory data."""
        data_summary = json.dumps(data, indent=2)

        prompt = f"""Analyze the following inventory data and provide actionable insights:

Data:
{data_summary}

Provide insights on:
1. Stock levels and trends
2. Potential issues or alerts
3. Optimization opportunities
4. Recommendations

Insights:"""

        return await self.generate_text(prompt, temperature=0.5)

    async def answer_inventory_question(self, question: str, inventory_context: List[Dict[str, Any]]) -> str:
        """Answer inventory-related questions with context."""
        # Format inventory context
        context_parts = []
        for item in inventory_context:
            context_parts.append(
                f"- {item.get('name', 'Unknown')}: "
                f"{item.get('quantity', 0)} units at "
                f"{item.get('location', 'Unknown location')}"
            )

        context = "\n".join(context_parts)

        system_prompt = """You are an AI assistant for inventory management. Answer questions accurately based on the provided inventory data. Be concise and specific."""

        return await self.query_with_context(question, context, system_prompt)

    async def stream_chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Stream chat responses (for real-time UI updates)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": self.model_id,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": True,
                    },
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data != "[DONE]":
                                try:
                                    chunk = json.loads(data)
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {str(e)}"

    async def health_check(self) -> bool:
        """Check if LLM service is available."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{self.base_url}/v1/health_check")
                return response.status_code == 200
        except:
            return False


# Global instance
llm_service = LLMService()
