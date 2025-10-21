"""
Python API wrapper for CogniDream engine
"""

import os
import json
import ctypes
from typing import Dict, List, Optional, Union
from datetime import datetime
import requests
from pydantic import BaseModel

class UserSession(BaseModel):
    session_id: str
    user_id: str
    model_id: str
    created_at: datetime
    last_activity: datetime
    requests_processed: int
    tokens_generated: int

class SystemMetrics(BaseModel):
    total_requests: int
    total_tokens: int
    active_sessions: int
    vram_usage: float
    avg_latency: float
    gpu_utilization: List[float]
    memory_utilization: List[float]

class ModelStats(BaseModel):
    model_id: str
    requests_processed: int
    tokens_generated: int
    avg_latency: float
    vram_usage: float
    gpu_utilization: float
    memory_utilization: float

class UserStats(BaseModel):
    user_id: str
    total_requests: int
    total_tokens: int
    active_sessions: int
    avg_latency: float

class CogniDreamAPI:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def create_session(self, user_id: str, model_id: str) -> UserSession:
        """Create a new user session"""
        response = self.session.post(
            f"{self.base_url}/api/v1/sessions",
            json={"user_id": user_id, "model_id": model_id}
        )
        response.raise_for_status()
        return UserSession(**response.json())

    def end_session(self, session_id: str) -> bool:
        """End a user session"""
        response = self.session.delete(f"{self.base_url}/api/v1/sessions/{session_id}")
        return response.status_code == 200

    def get_session_info(self, session_id: str) -> Optional[UserSession]:
        """Get information about a specific session"""
        response = self.session.get(f"{self.base_url}/api/v1/sessions/{session_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return UserSession(**response.json())

    def get_active_sessions(self) -> List[UserSession]:
        """Get all active sessions"""
        response = self.session.get(f"{self.base_url}/api/v1/sessions")
        response.raise_for_status()
        return [UserSession(**session) for session in response.json()]

    def get_system_metrics(self) -> SystemMetrics:
        """Get system-wide metrics"""
        response = self.session.get(f"{self.base_url}/api/v1/metrics")
        response.raise_for_status()
        return SystemMetrics(**response.json())

    def get_model_stats(self, model_id: str) -> Optional[ModelStats]:
        """Get statistics for a specific model"""
        response = self.session.get(f"{self.base_url}/api/v1/models/{model_id}/stats")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return ModelStats(**response.json())

    def update_model_config(self, model_id: str, config: Dict) -> bool:
        """Update configuration for a specific model"""
        response = self.session.put(
            f"{self.base_url}/api/v1/models/{model_id}/config",
            json=config
        )
        return response.status_code == 200

    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """Get statistics for a specific user"""
        response = self.session.get(f"{self.base_url}/api/v1/users/{user_id}/stats")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return UserStats(**response.json()) 