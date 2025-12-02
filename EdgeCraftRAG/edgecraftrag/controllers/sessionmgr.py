# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Any, Dict, List, Optional

from edgecraftrag.api_schema import SessionIn
from edgecraftrag.base import BaseMgr, InferenceType
from edgecraftrag.components.session import Session
from edgecraftrag.config_repository import MilvusConfigRepository
from edgecraftrag.env import SESSION_FILE


class SessionManager(BaseMgr):
    def __init__(self):
        super().__init__()
        self._current_session_id: Optional[str] = None
        self.session_file = SESSION_FILE

        self.milvus_repo = MilvusConfigRepository.create_connection(Repo_config_name="session_storage", max_retries=1)
        self.components: Dict[str, Session] = {}

        if self.milvus_repo and self.milvus_repo.connected:
            self._load_from_milvus()
        else:
            self.load_from_file()

    def set_current_session(self, session_id: str) -> None:
        self._current_session_id = session_id if session_id and session_id not in ("None", "") else "default_session"
        if self._current_session_id not in self.components:
            new_session = Session(self._current_session_id)
            self.add(new_session, name=self._current_session_id)

    def get_current_session(self) -> Optional[Session]:
        if not self._current_session_id:
            return None
        return self.components.get(self._current_session_id)

    def create_session(self, session: SessionIn) -> str:
        session_id = session.idx if session and session.idx else None

        if not session_id or session_id in ("", "None"):
            session_id = f"session_{len(self.components) + 1}"
            while session_id in self.components:
                session_id = f"session_{len(self.components) + 1}"

        if session_id in self.components:
            raise ValueError(f"Session ID {session_id} already exists")

        new_session = Session(session_id)
        self.add(new_session, name=session_id)
        return session_id

    def add(self, session: Session, name: str) -> None:
        self.components[name] = session
        if self.milvus_repo and self.milvus_repo.connected:
            self.milvus_repo.add_config_by_idx(name, session.to_dict())
        else:
            self.save_to_file()

    def clear_current_history(self) -> None:
        current_session = self.get_current_session()
        if current_session:
            current_session.clear_messages()
            self._persist_session(current_session.idx)

    def save_current_message(self, sessionid: str, role: str, content: str) -> str:
        current_session = self.get(sessionid)
        if not current_session:
            return "No current session set"

        try:
            current_session.add_message(role, content)
            self._persist_session(sessionid)
            return "Message added successfully"
        except ValueError as e:
            return f"Failed to add message: {str(e)}"

    def update_current_message(self, sessionid: str, role: str, content: str) -> str:
        current_session = self.get(sessionid)
        if not current_session:
            return "No current session set"
        try:
            current_session.update_current_message(role, content)
            return "Message updated successfully"
        except ValueError as e:
            return f"Failed to update message: {str(e)}"

    def concat_history(self, sessionid: str, inference_type: str, user_message: str) -> str:
        max_token = 6000
        if inference_type == InferenceType.VLLM:
            vllm_max_len = int(os.getenv("MAX_MODEL_LEN", "10240"))
            if vllm_max_len > 5000:
                max_token = vllm_max_len - 1024

        current_session = self.get(sessionid)
        if not current_session:
            return ""
        history_messages = current_session.get_messages()
        recent_str = self.get_recent_chat_rounds(history_messages)

        self.save_current_message(sessionid, "user", user_message)
        return recent_str[-max_token:] if len(recent_str) > max_token else recent_str

    def get_recent_chat_rounds(self, messages: List[Dict[str, str]]) -> str:
        history_num = int(os.getenv("CHAT_HISTORY_ROUND", "0"))
        if history_num <= 0:
            return ""
        total = len(messages)
        start_idx = max(0, total - (history_num * 2))
        return str(messages[start_idx:])

    def get_all_sessions(self):
        return {
            sid: session.get_user_message_titel()
            for sid, session in reversed(self.components.items())
            if isinstance(session, Session)
        }

    def get_session_by_id(self, session_id: str) -> Dict[str, Any]:
        session = self.get(session_id)
        if not session or not isinstance(session, Session):
            return {"session_id": session_id, "exists": False}
        return session.to_dict()

    def _persist_session(self, session_id: str):
        session = self.components.get(session_id)
        if not session:
            return

        if self.milvus_repo and self.milvus_repo.connected:
            self.milvus_repo.update_config_by_idx(session_id, session.to_dict())
        else:
            self.save_to_file()

    def save_to_file(self) -> Dict[str, str]:
        try:
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            data = {sid: session.to_dict() for sid, session in self.components.items() if isinstance(session, Session)}
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return {"status": "success", "message": f"Saved to {self.session_file}"}
        except Exception as e:
            return {"status": "error", "message": f"Save failed: {str(e)}"}

    def load_from_file(self) -> Dict[str, str]:
        try:
            if not os.path.exists(self.session_file):
                return {"status": "warning", "message": "Session file does not exist"}
            with open(self.session_file, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            if not isinstance(loaded_data, dict):
                raise ValueError("Invalid session file format: expected dict")

            self.components.clear()
            for session_id, session_data in loaded_data.items():
                session = Session.from_dict(session_data)
                self.components[session_id] = session
            return {
                "status": "success",
                "message": f"Loaded {len(self.components)} sessions from {self.session_file}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Load failed: {str(e)}"}

    def _load_from_milvus(self):
        try:
            milvus_sessions = self.milvus_repo.get_configs()
            for item in milvus_sessions:
                session_id = item.get("idx")
                config_json = item.get("config_json", {})
                if session_id and isinstance(config_json, dict):
                    session = Session.from_dict(config_json)
                    self.components[session_id] = session
            print(f"Loaded {len(self.components)} sessions from Milvus.")
        except Exception as e:
            print(f"Error loading sessions from Milvus: {str(e)}")
