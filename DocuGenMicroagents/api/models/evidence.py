"""
Evidence Packet - Central Evidence Store for README Generation

This module defines the schema for storing all repository evidence
with provenance tracking to prevent hallucinations.

Key Principles:
- Single source of truth for all README content
- Every evidence item includes source_files for traceability
- Deterministic derivation (no LLM-generated values)
- Supports both file-based and structured agent outputs
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class EvidenceItem:
    """Single piece of evidence with provenance."""
    category: str  # "dependency", "config", "route", "tool", etc.
    key: str  # Identifier (e.g., "fastapi", "PORT", "/upload")
    value: str  # The evidence value
    source_files: List[str] = field(default_factory=list)  # Where it was found
    confidence: str = "high"  # "high", "medium", "low"


@dataclass
class EvidencePacket:
    """
    Central evidence store for README generation.

    Contains all factual information extracted from repository
    with provenance tracking.
    """

    # Repository metadata (deterministic)
    repo_name: str = ""
    repo_path: str = ""

    # Language detection
    languages: Dict[str, int] = field(default_factory=dict)  # {language: file_count}

    # Dependencies (from package files)
    python_deps: List[str] = field(default_factory=list)  # From requirements.txt
    node_deps: List[str] = field(default_factory=list)  # From package.json

    # Technology flags
    has_docker: bool = False
    has_frontend: bool = False
    has_backend: bool = False

    # Configuration
    env_files: List[str] = field(default_factory=list)  # [".env.example", ".env"]
    env_vars: Dict[str, str] = field(default_factory=dict)  # {VAR: description}

    # Docker evidence
    docker_files: List[str] = field(default_factory=list)  # ["Dockerfile", "docker-compose.yml"]

    # API endpoints (if backend detected)
    api_endpoints: List[Dict[str, str]] = field(default_factory=list)  # [{method, path, file}]

    # Entry points
    entry_points: List[str] = field(default_factory=list)  # ["server.py", "main.py"]

    # Frontend info
    frontend_framework: str = ""  # "React", "Vue", "Angular", ""
    frontend_files: List[str] = field(default_factory=list)

    # Raw evidence items
    items: List[EvidenceItem] = field(default_factory=list)

    def add_evidence(self, item: EvidenceItem) -> None:
        """Add evidence item with deduplication."""
        # Avoid duplicate evidence
        for existing in self.items:
            if existing.key == item.key and existing.category == item.category:
                return
        self.items.append(item)

    def has_evidence_for(self, key: str, category: str = None) -> bool:
        """Check if evidence exists for a key."""
        for item in self.items:
            if item.key == key:
                if category is None or item.category == category:
                    return True
        return False

    def get_evidence(self, key: str, category: str = None) -> List[EvidenceItem]:
        """Get all evidence items matching key and optional category."""
        results = []
        for item in self.items:
            if item.key == key:
                if category is None or item.category == category:
                    results.append(item)
        return results

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_name": self.repo_name,
            "repo_path": self.repo_path,
            "languages": self.languages,
            "python_deps": self.python_deps,
            "node_deps": self.node_deps,
            "has_docker": self.has_docker,
            "has_frontend": self.has_frontend,
            "has_backend": self.has_backend,
            "env_files": self.env_files,
            "env_vars": self.env_vars,
            "docker_files": self.docker_files,
            "api_endpoints": self.api_endpoints,
            "entry_points": self.entry_points,
            "frontend_framework": self.frontend_framework,
            "frontend_files": self.frontend_files,
            "items": [
                {
                    "category": item.category,
                    "key": item.key,
                    "value": item.value,
                    "source_files": item.source_files,
                    "confidence": item.confidence
                }
                for item in self.items
            ]
        }
