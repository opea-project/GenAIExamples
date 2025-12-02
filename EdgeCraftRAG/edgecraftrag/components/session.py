# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import Any, Dict, List, Optional

from edgecraftrag.base import BaseComponent, CompType
from pydantic import model_serializer


class Session(BaseComponent):
    def __init__(self, session_id: str):
        super().__init__(comp_type=CompType.SESSION)
        self.session_id = session_id
        self.messages: List[Dict[str, str]] = []
        self.created_at: datetime = datetime.now()
        self.current_messages: Optional[Dict[str, str]] = None

    def add_message(self, role: str, content: str) -> None:
        if role not in ("user", "assistant"):
            raise ValueError("Role should be 'user' or 'assistant'")
        self.messages.append({"role": role, "content": content})
        self.current_messages = None

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages.copy()

    def clear_messages(self) -> None:
        self.messages = []

    def get_user_message_titel(self) -> Optional[str]:
        for msg in self.messages:
            if msg["role"] == "user":
                return msg["content"]
        return None

    def to_dict(self) -> Dict[str, Any]:
        concat_messages = self.messages.copy()
        if self.current_messages:
            concat_messages.append(self.current_messages)
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": concat_messages,
            "idx": self.idx,
        }

    def update_current_message(self, role: str, content: str) -> None:
        self.current_messages = {"role": role, "content": content}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        session_id = data.get("session_id", f"session_{data.get('idx', 'unknown')}")
        session = cls(session_id)
        session.idx = data.get("idx", session.idx)
        created_at_str = data.get("created_at")
        session.created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
        for item in data.get("messages", []):
            if isinstance(item, dict) and "role" in item and "content" in item:
                role = item["role"]
                content = item["content"]
                if role in ("user", "assistant") and isinstance(content, str):
                    session.add_message(role, content)
        return session

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": self.messages,
        }
