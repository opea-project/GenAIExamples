# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, List, Optional

import gc
from edgecraftrag.api_schema import KnowledgeBaseCreateIn
from edgecraftrag.base import BaseMgr
from edgecraftrag.components.knowledge_base import Knowledge
from fastapi import HTTPException, status


class KnowledgeManager(BaseMgr):
    def __init__(self):
        super().__init__()
        self.active_knowledge_idx: Optional[List[str]] = []
        self.active_experience_idx: Optional[str] = None

    def get_knowledge_base_by_name_or_id(self, name: str):
        for _, kb in self.components.items():
            if kb.name == name or kb.idx == name:
                return kb
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="knowledge base does not exist")

    def get_active_knowledge_base(self) -> Optional[List[Knowledge]]:
        active_kbs = []
        for idx in self.active_knowledge_idx:
            active_kbs.append(self.get_knowledge_base_by_name_or_id(idx))
        return active_kbs

    def get_active_experience(self):
        if self.active_experience_idx:
            return self.get_knowledge_base_by_name_or_id(self.active_experience_idx)
        else:
            return None

    def active_knowledge(self, knowledge: KnowledgeBaseCreateIn):
        kb = self.get_knowledge_base_by_name_or_id(knowledge.name)
        if kb.comp_type != "knowledge":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Experience type  cannot be active")
        self.active_knowledge_idx.append(kb.idx)
        kb.active = True
        return kb

    def deactive_knowledge(self, knowledge: KnowledgeBaseCreateIn):
        kb = self.get_knowledge_base_by_name_or_id(knowledge.name)
        if kb.idx in self.active_knowledge_idx:
            self.active_knowledge_idx.remove(kb.idx)
        kb.active = False
        return kb

    def active_experience(self, knowledge: KnowledgeBaseCreateIn):
        kb = self.get_knowledge_base_by_name_or_id(knowledge.name)
        if kb.comp_type != "experience":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Knowledge type  cannot be active")
        self.active_experience_idx = kb.idx if knowledge.experience_active else None
        if kb.experience_active != knowledge.experience_active:
            for idx, comp in self.components.items():
                if isinstance(comp, Knowledge):
                    comp.experience_active = idx == self.active_experience_idx
        return kb

    def create_knowledge_base(self, knowledge: KnowledgeBaseCreateIn, origin_json: str) -> Knowledge:
        for _, kb in self.components.items():
            if kb.name == knowledge.name:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The knowledge base already exists.")
            if knowledge.comp_type == "experience":
                for _, kb in self.components.items():
                    if kb.comp_type == "experience":
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT, detail="Only one experience class can be created."
                        )
        if knowledge.comp_type == "experience":
            knowledge.active = False
        if knowledge.active is None:
            knowledge.active = False
        kb = Knowledge(
            idx=knowledge.idx,
            name=knowledge.name,
            description=knowledge.description,
            active=knowledge.active,
            comp_type=knowledge.comp_type,
            comp_subtype=knowledge.comp_subtype,
            experience_active=knowledge.experience_active,
            all_document_maps=knowledge.all_document_maps,
            file_paths=knowledge.file_paths,
            origin_json=origin_json,
        )
        self.add(kb)
        if knowledge.active:
            self.active_knowledge(knowledge)
        if knowledge.experience_active:
            self.active_experience(knowledge)
        return kb

    def delete_knowledge_base(self, name: str):
        kb = self.get_knowledge_base_by_name_or_id(name)
        kb.node_parser = None
        kb.indexer = None
        self.remove(kb.idx)
        del kb
        gc.collect()
        return "Knowledge base removed successfully"

    def update_knowledge_base(self, knowledge, active_pl=None) -> Knowledge:
        kb = self.get_knowledge_base_by_name_or_id(knowledge.name)
        if knowledge.active is None:
            knowledge.active = False
            kb.update_knowledge_json({"active": knowledge.active})
        if kb.comp_type == "knowledge":
            if knowledge.description is not None:
                kb.description = knowledge.description
            if kb.active != knowledge.active:
                kb = self.active_knowledge(knowledge) if knowledge.active else self.deactive_knowledge(knowledge)
                if active_pl:
                    active_pl.update_retriever_list(self.get_active_knowledge_base())

        if kb.comp_type == "experience":
            if knowledge.description is not None:
                kb.description = knowledge.description
            if knowledge.experience_active is not None and kb.experience_active != knowledge.experience_active:
                kb = self.active_experience(knowledge)
        return "Knowledge base update successfully"

    def get_all_knowledge_bases(self) -> List[Dict[str, Any]]:
        kb_list = []
        for idx, kb in self.components.items():
            kb_list.append(kb)
        return kb_list

    def get_experience_kb(self):
        for idx, kb in self.components.items():
            if kb.comp_type == "experience":
                return kb
