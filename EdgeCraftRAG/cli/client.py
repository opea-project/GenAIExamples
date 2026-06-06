# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests


class EcragApiClient:
    """API client for Edge Craft RAG."""

    def __init__(self, host: str = "http://localhost", server_port: int = 16010, mega_port: int = 16011):
        """Initialize the API client.

        Args:
            host: The host URL (default: http://localhost)
            server_port: The server port (default: 16010)
            mega_port: The mega service port (default: 16011)
        """
        # Normalize host URL
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"

        # Remove trailing slash if present
        host = host.rstrip("/")

        self.server_url = f"{host}:{server_port}"
        self.mega_url = f"{host}:{mega_port}"

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request."""
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    # Pipeline Management
    def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pipeline."""
        url = urljoin(self.server_url, "/v1/settings/pipelines")
        return self._request("POST", url, json=pipeline_data, headers={"Content-Type": "application/json"})

    def get_pipelines(self, gen_type: Optional[str] = None) -> Dict[str, Any]:
        """Get all pipelines."""
        url = urljoin(self.server_url, "/v1/settings/pipelines")
        params = {"gen_type": gen_type} if gen_type else {}
        return self._request("GET", url, params=params, headers={"Content-Type": "application/json"})

    def get_pipeline(self, name: str) -> Dict[str, Any]:
        """Get a specific pipeline."""
        url = urljoin(self.server_url, f"/v1/settings/pipelines/{name}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_pipeline_json(self, name: str) -> Dict[str, Any]:
        """Get pipeline JSON data."""
        url = urljoin(self.server_url, f"/v1/settings/pipelines/{name}/json")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def update_pipeline(self, name: str, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a pipeline."""
        url = urljoin(self.server_url, f"/v1/settings/pipelines/{name}")
        return self._request("PATCH", url, json=pipeline_data, headers={"Content-Type": "application/json"})

    def activate_pipeline(self, name: str) -> Dict[str, Any]:
        """Activate a pipeline."""
        return self.update_pipeline(name, {"active": True})

    def deactivate_pipeline(self, name: str) -> Dict[str, Any]:
        """Deactivate a pipeline."""
        return self.update_pipeline(name, {"active": False})

    def delete_pipeline(self, name: str) -> Dict[str, Any]:
        """Delete a pipeline."""
        url = urljoin(self.server_url, f"/v1/settings/pipelines/{name}")
        return self._request("DELETE", url, headers={"Content-Type": "application/json"})

    def get_pipeline_benchmark(self) -> Dict[str, Any]:
        """Get the active pipeline's benchmark."""
        url = urljoin(self.server_url, "/v1/settings/pipeline/benchmark")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_pipeline_benchmarks(self, name: str) -> Dict[str, Any]:
        """Get a specific pipeline's benchmark."""
        url = urljoin(self.server_url, f"/v1/settings/pipelines/{name}/benchmarks")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def import_pipeline(self, file_path: str) -> Dict[str, Any]:
        """Import pipeline from a JSON file."""
        url = urljoin(self.server_url, "/v1/settings/pipelines/import")
        with open(file_path, "rb") as f:
            return self._request("POST", url, files={"file": f})

    # Model Management
    def load_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load a model."""
        url = urljoin(self.server_url, "/v1/settings/models")
        return self._request("POST", url, json=model_data, headers={"Content-Type": "application/json"})

    def get_models(self) -> Dict[str, Any]:
        """Get all models."""
        url = urljoin(self.server_url, "/v1/settings/models")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get a specific model."""
        url = urljoin(self.server_url, f"/v1/settings/models/{model_id}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def update_model(self, model_id: str, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a model."""
        url = urljoin(self.server_url, f"/v1/settings/models/{model_id}")
        return self._request("PATCH", url, json=model_data, headers={"Content-Type": "application/json"})

    def delete_model(self, model_id: str) -> Dict[str, Any]:
        """Delete a model."""
        url = urljoin(self.server_url, f"/v1/settings/models/{model_id}")
        return self._request("DELETE", url, headers={"Content-Type": "application/json"})

    def get_model_weights(self, model_id: str) -> Dict[str, Any]:
        """Get available model weights."""
        url = urljoin(self.server_url, f"/v1/settings/weight/{model_id}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_available_models(self, model_type: str, server_address: Optional[str] = None) -> Dict[str, Any]:
        """Get available models by type."""
        url = urljoin(self.server_url, f"/v1/settings/avail-models/{model_type}")
        params = {"server_address": server_address} if server_address else {}
        return self._request("GET", url, params=params, headers={"Content-Type": "application/json"})

    # Knowledge Base Management
    def create_knowledge_base(self, kb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a knowledge base."""
        url = urljoin(self.server_url, "/v1/knowledge")
        return self._request("POST", url, json=kb_data, headers={"Content-Type": "application/json"})

    def get_knowledge_bases(self) -> Dict[str, Any]:
        """Get all knowledge bases."""
        url = urljoin(self.server_url, "/v1/knowledge")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_knowledge_base(self, kb_name: str) -> Dict[str, Any]:
        """Get a specific knowledge base."""
        url = urljoin(self.server_url, f"/v1/knowledge/{kb_name}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_knowledge_base_json(self, kb_name: str) -> Dict[str, Any]:
        """Get knowledge base JSON data."""
        url = urljoin(self.server_url, f"/v1/knowledge/{kb_name}/json")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_knowledge_base_filemap(self, kb_name: str, page_num: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get knowledge base file map."""
        url = urljoin(self.server_url, f"/v1/knowledge/{kb_name}/filemap")
        params = {"page_num": page_num, "page_size": page_size}
        return self._request("GET", url, params=params, headers={"Content-Type": "application/json"})

    def update_knowledge_base(self, kb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a knowledge base."""
        url = urljoin(self.server_url, "/v1/knowledge/patch")
        return self._request("PATCH", url, json=kb_data, headers={"Content-Type": "application/json"})

    def delete_knowledge_base(self, kb_name: str) -> Dict[str, Any]:
        """Delete a knowledge base."""
        url = urljoin(self.server_url, f"/v1/knowledge/{kb_name}")
        return self._request("DELETE", url, headers={"Content-Type": "application/json"})

    def add_files_to_kb(self, kb_name: str, local_paths: list) -> Dict[str, Any]:
        """Add files to a knowledge base."""
        url = urljoin(self.server_url, f"/v1/knowledge/{kb_name}/files")
        return self._request(
            "POST", url, json={"local_paths": local_paths}, headers={"Content-Type": "application/json"}
        )

    def delete_files_from_kb(self, kb_name: str, local_paths: list) -> Dict[str, Any]:
        """Delete files from a knowledge base."""
        url = urljoin(self.server_url, f"/v1/knowledge/{kb_name}/files")
        return self._request(
            "DELETE", url, json={"local_paths": local_paths}, headers={"Content-Type": "application/json"}
        )

    # Experience Management
    def get_experiences(self) -> Dict[str, Any]:
        """Get all experiences."""
        url = urljoin(self.server_url, "/v1/experiences")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_experience(self, exp_id: str) -> Dict[str, Any]:
        """Get a specific experience."""
        url = urljoin(self.server_url, "/v1/experience")
        return self._request("POST", url, json={"idx": exp_id}, headers={"Content-Type": "application/json"})

    def create_experience(self, exp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an experience."""
        return self.update_experience(exp_data)

    def update_experience(self, exp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an experience."""
        url = urljoin(self.server_url, "/v1/experiences")
        return self._request("PATCH", url, json=exp_data, headers={"Content-Type": "application/json"})

    def delete_experience(self, exp_id: str) -> Dict[str, Any]:
        """Delete an experience."""
        url = urljoin(self.server_url, "/v1/experiences")
        return self._request("DELETE", url, json={"idx": exp_id}, headers={"Content-Type": "application/json"})

    def add_experiences_from_file(self, file_path: str) -> Dict[str, Any]:
        """Add experiences from a file."""
        url = urljoin(self.server_url, "/v1/experiences/files")
        return self._request("POST", url, json={"local_path": file_path}, headers={"Content-Type": "application/json"})

    def check_multiple_experiences(self, experiences: list) -> Dict[str, Any]:
        """Check multiple experiences for duplicates."""
        url = urljoin(self.server_url, "/v1/multiple_experiences/check")
        return self._request("POST", url, json=experiences, headers={"Content-Type": "application/json"})

    def confirm_multiple_experiences(self, experiences: list, flag: bool = True) -> Dict[str, Any]:
        """Confirm multiple experiences."""
        url = urljoin(self.server_url, f"/v1/multiple_experiences/confirm?flag={flag}")
        return self._request("POST", url, json=experiences, headers={"Content-Type": "application/json"})

    # Agent Management
    def get_agents(self) -> Dict[str, Any]:
        """Get all agents."""
        url = urljoin(self.server_url, "/v1/agents")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get a specific agent."""
        url = urljoin(self.server_url, f"/v1/agents/{agent_name}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_agent_configs(self, agent_type: str) -> Dict[str, Any]:
        """Get default configs for an agent type."""
        url = urljoin(self.server_url, f"/v1/agents/configs/{agent_type}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an agent."""
        url = urljoin(self.server_url, "/v1/agents")
        return self._request("POST", url, json=agent_data, headers={"Content-Type": "application/json"})

    def update_agent(self, agent_name: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an agent."""
        url = urljoin(self.server_url, f"/v1/agents/{agent_name}")
        return self._request("PATCH", url, json=agent_data, headers={"Content-Type": "application/json"})

    def delete_agent(self, agent_name: str) -> Dict[str, Any]:
        """Delete an agent."""
        url = urljoin(self.server_url, f"/v1/agents/{agent_name}")
        return self._request("DELETE", url, headers={"Content-Type": "application/json"})

    # Prompt Management
    def get_prompt(self) -> Dict[str, Any]:
        """Get the current system prompt."""
        url = urljoin(self.server_url, "/v1/chatqna/prompt")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_tagged_prompt(self) -> Dict[str, Any]:
        """Get the tagged system prompt."""
        url = urljoin(self.server_url, "/v1/chatqna/prompt/tagged")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_default_prompt(self) -> Dict[str, Any]:
        """Get the default system prompt."""
        url = urljoin(self.server_url, "/v1/chatqna/prompt/default")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def update_prompt(self, prompt: str) -> Dict[str, Any]:
        """Update the system prompt."""
        url = urljoin(self.server_url, "/v1/chatqna/prompt")
        return self._request("POST", url, json={"prompt": prompt}, headers={"Content-Type": "application/json"})

    def upload_prompt_from_file(self, file_path: str) -> Dict[str, Any]:
        """Upload system prompt from a file."""
        url = urljoin(self.server_url, "/v1/chatqna/prompt-file")
        with open(file_path, "rb") as f:
            return self._request("POST", url, files={"file": f})

    def reset_prompt(self) -> Dict[str, Any]:
        """Reset system prompt to default."""
        url = urljoin(self.server_url, "/v1/chatqna/prompt/reset")
        return self._request("POST", url, headers={"Content-Type": "application/json"})

    # Data Management
    def get_nodes(self) -> Dict[str, Any]:
        """Get all nodes in the active knowledge base."""
        url = urljoin(self.server_url, "/v1/data/nodes")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_nodes_by_document(self, document_name: str) -> Dict[str, Any]:
        """Get nodes by document name."""
        url = urljoin(self.server_url, f"/v1/data/{document_name}/nodes")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_documents(self) -> Dict[str, Any]:
        """Get all document names in the active knowledge base."""
        url = urljoin(self.server_url, "/v1/data/documents")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_files(self) -> Dict[str, Any]:
        """Get all files."""
        url = urljoin(self.server_url, "/v1/data/files")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_file(self, file_name: str) -> Dict[str, Any]:
        """Get a specific file."""
        url = urljoin(self.server_url, f"/v1/data/files/{file_name}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def upload_file(self, file_name: str, file_path: str) -> Dict[str, Any]:
        """Upload a file."""
        url = urljoin(self.server_url, f"/v1/data/file/{file_name}")
        with open(file_path, "rb") as f:
            return self._request("POST", url, files={"file": f})

    # Session Management
    def get_sessions(self) -> Dict[str, Any]:
        """Get all sessions."""
        url = urljoin(self.server_url, "/v1/sessions")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get a specific session."""
        url = urljoin(self.server_url, f"/v1/session/{session_id}")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    # System Information
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        url = urljoin(self.server_url, "/v1/system/info")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    def get_available_devices(self) -> Dict[str, Any]:
        """Get available inference devices."""
        url = urljoin(self.server_url, "/v1/system/device")
        return self._request("GET", url, headers={"Content-Type": "application/json"})

    # Chat/Query APIs
    def retrieval(self, messages: str, top_n: int = 5, max_tokens: int = 512) -> Dict[str, Any]:
        """Retrieve relevant context chunks."""
        url = urljoin(self.server_url, "/v1/retrieval")
        return self._request(
            "POST",
            url,
            json={"messages": messages, "top_n": top_n, "max_tokens": max_tokens},
            headers={"Content-Type": "application/json"},
        )

    def chatqna(self, messages: str, top_n: int = 5, max_tokens: int = 512) -> Dict[str, Any]:
        """Run full RAG pipeline through mega service."""
        url = urljoin(self.mega_url, "/v1/chatqna")
        return self._request(
            "POST",
            url,
            json={"messages": messages, "top_n": top_n, "max_tokens": max_tokens},
            headers={"Content-Type": "application/json"},
        )

    def ragqna(self, messages: str, top_n: int = 5, max_tokens: int = 512, stream: bool = False) -> Dict[str, Any]:
        """Run RAG pipeline with contexts in response."""
        url = urljoin(self.server_url, "/v1/ragqna")
        return self._request(
            "POST",
            url,
            json={"messages": messages, "top_n": top_n, "max_tokens": max_tokens, "stream": stream},
            headers={"Content-Type": "application/json"},
        )

    def check_vllm_connection(self, server_address: str, model_name: str) -> Dict[str, Any]:
        """Check vLLM server connection."""
        url = urljoin(self.server_url, "/v1/check/vllm")
        return self._request(
            "POST",
            url,
            json={"server_address": server_address, "model_name": model_name},
            headers={"Content-Type": "application/json"},
        )
