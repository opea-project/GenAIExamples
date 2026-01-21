# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OPEA DocSummarization Service Handles document summarization and analysis."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from .llm_service import llm_service

logger = logging.getLogger(__name__)


class DocSummarizationService:
    """Document summarization using OPEA LLM service."""

    def __init__(self):
        self.base_url = os.getenv("OPEA_LLM_URL", "http://llm-service:9000")
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def summarize_document(
        self, text: str, summary_type: str = "concise", max_length: int = 200
    ) -> Dict[str, Any]:
        """Summarize a document.

        Args:
            text: Document text to summarize
            summary_type: "concise", "detailed", or "bullet_points"
            max_length: Maximum length in words

        Returns:
            Summary with metadata
        """
        try:
            if summary_type == "bullet_points":
                prompt = f"""Summarize the following text as bullet points ({max_length} words max):

{text}

Key Points:
•"""
            elif summary_type == "detailed":
                prompt = f"""Provide a detailed summary of the following text ({max_length} words max):

{text}

Detailed Summary:"""
            else:  # concise
                prompt = f"""Provide a concise summary of the following text ({max_length} words max):

{text}

Summary:"""

            summary = await llm_service.generate_text(prompt, temperature=0.3)

            # Add bullet point if needed
            if summary_type == "bullet_points" and not summary.strip().startswith("•"):
                summary = "• " + summary

            return {
                "success": True,
                "original_length": len(text.split()),
                "summary": summary.strip(),
                "summary_length": len(summary.split()),
                "compression_ratio": round(len(summary.split()) / max(len(text.split()), 1), 2),
                "type": summary_type,
            }

        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {"success": False, "error": str(e)}

    async def summarize_inventory_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize inventory report data Specialized for inventory metrics."""
        try:
            # Convert report data to narrative text
            report_text = self._format_report_for_summarization(report_data)

            prompt = f"""Analyze this inventory report and provide:
1. Overall status summary
2. Key trends and patterns
3. Critical alerts or issues
4. Recommendations

Report Data:
{report_text}

Analysis:"""

            analysis = await llm_service.generate_text(prompt, temperature=0.4)

            return {
                "success": True,
                "report_summary": analysis,
                "data": report_data,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Report summarization error: {e}")
            return {"success": False, "error": str(e)}

    def _format_report_for_summarization(self, report_data: Dict[str, Any]) -> str:
        """Format report data into readable text."""
        parts = []

        if "total_items" in report_data:
            parts.append(f"Total Items: {report_data['total_items']}")

        if "warehouses" in report_data:
            parts.append(f"Warehouses: {report_data['warehouses']}")

        if "stock_by_category" in report_data:
            parts.append("\nStock by Category:")
            for cat in report_data["stock_by_category"]:
                parts.append(f"  - {cat['category']}: {cat['count']} units ({cat['percentage']}%)")

        if "recent_activity" in report_data:
            parts.append("\nRecent Activity:")
            for activity in report_data["recent_activity"][:5]:
                parts.append(f"  - {activity['type']}: {activity['details']}")

        return "\n".join(parts)

    async def extract_key_information(self, text: str) -> Dict[str, Any]:
        """Extract structured information from unstructured text Useful for processing uploaded documents."""
        prompt = f"""Extract key information from the following text and return as JSON:

Text:
{text}

Extract:
- Products mentioned (name, SKU if available)
- Quantities
- Locations/warehouses
- Dates
- Actions or events

Return JSON format:
{{
  "products": [],
  "quantities": [],
  "locations": [],
  "dates": [],
  "events": []
}}

JSON:"""

        try:
            response = await llm_service.generate_text(prompt, temperature=0.1)

            # Parse JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].strip()
            else:
                json_str = response.strip()

            extracted = json.loads(json_str)

            return {"success": True, "extracted_info": extracted}

        except Exception as e:
            logger.error(f"Information extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def summarize_csv_data(self, csv_path: str, sample_size: int = 100) -> Dict[str, Any]:
        """Summarize CSV file contents."""
        try:
            df = pd.read_csv(csv_path)

            # Get basic stats
            stats = {
                "rows": len(df),
                "columns": list(df.columns),
                "numeric_summary": df.describe().to_dict() if len(df) > 0 else {},
                "sample": df.head(5).to_dict("records") if len(df) > 0 else [],
            }

            # Generate natural language summary
            stats_text = json.dumps(stats, indent=2, default=str)

            summary = await self.summarize_document(
                text=f"CSV File Analysis:\n{stats_text}",
                summary_type="bullet_points",
                max_length=150,
            )

            return {
                "success": True,
                "file": csv_path,
                "statistics": stats,
                "summary": (summary["summary"] if summary["success"] else "Summary unavailable"),
            }

        except Exception as e:
            logger.error(f"CSV summarization error: {e}")
            return {"success": False, "error": str(e)}

    async def generate_report_narrative(self, title: str, data_points: List[Dict[str, Any]]) -> str:
        """Generate narrative report from data points."""
        data_text = "\n".join([f"- {dp.get('label', 'Item')}: {dp.get('value', 'N/A')}" for dp in data_points])

        prompt = f"""Generate a professional narrative report titled "{title}" based on the following data:

{data_text}

Write a clear, professional report that explains the data, identifies trends, and provides insights:"""

        narrative = await llm_service.generate_text(prompt, temperature=0.5)
        return narrative


# Global instance
doc_summarization = DocSummarizationService()
