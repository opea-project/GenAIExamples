# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, List, Optional

from edgecraftrag.api_schema import KnowledgeBaseCreateIn
from edgecraftrag.base import BaseMgr
from edgecraftrag.components.knowledge_base import Knowledge
from fastapi import HTTPException, status


class KnowledgeManager(BaseMgr):
    def __init__(self):
        super().__init__()
        self.active_knowledge_idx: Optional[str] = None

    def get_knowledge_base_by_name_or_id(self, name: str):
        for _, kb in self.components.items():
            if kb.name == name or kb.idx == name:
                return kb
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge base does not exist")

    def get_active_knowledge_base(self) -> Optional[Knowledge]:
        if self.active_knowledge_idx:
            return self.get_knowledge_base_by_name_or_id(self.active_knowledge_idx)
        else:
            return None

    def active_knowledge(self, knowledge: KnowledgeBaseCreateIn):
        kb = self.get_knowledge_base_by_name_or_id(knowledge.name)
        self.active_knowledge_idx = kb.idx if knowledge.active else None

        for idx, comp in self.components.items():
            if isinstance(comp, Knowledge):
                comp.active = idx == self.active_knowledge_idx
        return kb

    def create_knowledge_base(self, knowledge: KnowledgeBaseCreateIn) -> Knowledge:
        for _, kb in self.components.items():
            if kb.name == knowledge.name:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The knowledge base already exists.")
        if knowledge.active is None:
            knowledge.active = False
        kb = Knowledge(name=knowledge.name, description=knowledge.description, active=knowledge.active)
        self.add(kb)
        if knowledge.active:
            self.active_knowledge(knowledge)
        return kb

    def delete_knowledge_base(self, name: str):
        kb = self.get_knowledge_base_by_name_or_id(name)
        if kb.idx == self.active_knowledge_idx:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot delete a running knowledge base."
            )
        self.remove(kb.idx)
        return "Knowledge base removed successfully"

    def update_knowledge_base(self, knowledge) -> Knowledge:
        kb = self.get_knowledge_base_by_name_or_id(knowledge.name)

        if knowledge.description is not None:
            kb.description = knowledge.description

        if knowledge.active is not None and kb.active != knowledge.active:
            kb = self.active_knowledge(knowledge)
        return "Knowledge base update successfully"

    def get_all_knowledge_bases(self) -> List[Dict[str, Any]]:
        kb_list = []
        for idx, kb in self.components.items():
            kb_list.append(kb)
        return kb_list
