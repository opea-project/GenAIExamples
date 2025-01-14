# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import uuid
from datetime import datetime
from typing import List, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.store.memory import InMemoryStore
from pydantic import BaseModel


class PersistenceConfig(BaseModel):
    checkpointer: bool = False
    store: bool = False


class PersistenceInfo(BaseModel):
    user_id: str = None
    thread_id: str = None
    started_at: datetime


class AgentPersistence:
    def __init__(self, config: PersistenceConfig):
        # for short-term memory
        self.checkpointer = None
        # for long-term memory
        self.store = None
        self.config = config
        print(f"Initializing AgentPersistence: {config}")
        self.initialize()

    def initialize(self) -> None:
        if self.config.checkpointer:
            self.checkpointer = MemorySaver()
        if self.config.store:
            self.store = InMemoryStore()

    def save(
        self,
        config: RunnableConfig,
        content: str,
        context: str,
        memory_id: Optional[str] = None,
    ):
        """This function is only for long-term memory."""
        mem_id = memory_id or uuid.uuid4()
        user_id = config["configurable"]["user_id"]
        self.store.put(
            ("memories", user_id),
            key=str(mem_id),
            value={"content": content, "context": context},
        )
        return f"Stored memory {content}"

    def get(self, config: RunnableConfig):
        """This function is only for long-term memory."""
        user_id = config["configurable"]["user_id"]
        namespace = ("memories", user_id)
        memories = self.store.search(namespace)
        return memories

    def update_state(self, config, graph: StateGraph):
        pass
