# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""CSV Data Processor Ingests CSV files and prepares them for OPEA knowledge base."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Process CSV files for inventory data."""

    def __init__(self, data_dir: str = "/data"):
        self.data_dir = Path(data_dir)
        self.processed_data = {}

    def load_all_csv_files(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from the data directory."""
        csv_files = list(self.data_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files")

        dataframes = {}
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                dataframes[csv_file.stem] = df
                logger.info(f"Loaded {csv_file.name}: {len(df)} rows")
            except Exception as e:
                logger.error(f"Error loading {csv_file.name}: {e}")

        return dataframes

    def prepare_for_embedding(self, dataframes: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Prepare data for OPEA embedding service."""
        documents = []

        for name, df in dataframes.items():
            for idx, row in df.iterrows():
                # Create a text representation of the row
                text_parts = []
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value):
                        text_parts.append(f"{col}: {value}")

                doc_text = " | ".join(text_parts)

                documents.append(
                    {
                        "id": f"{name}_{idx}",
                        "source": name,
                        "text": doc_text,
                        "metadata": row.to_dict(),
                    }
                )

        logger.info(f"Prepared {len(documents)} documents for embedding")
        return documents

    def extract_inventory_data(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Extract structured inventory data."""
        inventory_data = {
            "products": [],
            "categories": set(),
            "warehouses": set(),
            "total_items": 0,
        }

        for name, df in dataframes.items():
            # Try to identify inventory-related columns
            if any(col in df.columns for col in ["product", "Product", "item", "Item"]):
                for _, row in df.iterrows():
                    product_info = {"source": name, "data": row.to_dict()}
                    inventory_data["products"].append(product_info)
                    inventory_data["total_items"] += 1

                    # Extract categories if available
                    if "category" in df.columns or "Category" in df.columns:
                        cat_col = "category" if "category" in df.columns else "Category"
                        if pd.notna(row[cat_col]):
                            inventory_data["categories"].add(str(row[cat_col]))

        inventory_data["categories"] = list(inventory_data["categories"])
        inventory_data["warehouses"] = list(inventory_data["warehouses"])

        return inventory_data

    def create_knowledge_base(self) -> Dict[str, Any]:
        """Create a complete knowledge base from CSV data."""
        dataframes = self.load_all_csv_files()

        knowledge_base = {
            "documents": self.prepare_for_embedding(dataframes),
            "inventory": self.extract_inventory_data(dataframes),
            "metadata": {
                "total_files": len(dataframes),
                "total_documents": sum(len(df) for df in dataframes.values()),
                "files": [name for name in dataframes.keys()],
            },
        }

        # Save processed data
        output_dir = self.data_dir / "processed"
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "knowledge_base.json", "w") as f:
            json.dump(knowledge_base, f, indent=2, default=str)

        logger.info(f"Knowledge base created with {len(knowledge_base['documents'])} documents")

        return knowledge_base

    def get_product_summary(self) -> Dict[str, Any]:
        """Get a summary of products for quick access."""
        dataframes = self.load_all_csv_files()

        summary = {"total_files": len(dataframes), "file_details": []}

        for name, df in dataframes.items():
            file_info = {
                "name": name,
                "rows": len(df),
                "columns": list(df.columns),
                "sample": df.head(3).to_dict("records") if len(df) > 0 else [],
            }
            summary["file_details"].append(file_info)

        return summary


# Global CSV processor instance
csv_processor = CSVProcessor(data_dir=os.getenv("CSV_DATA_DIR", "../data"))
