# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import uuid
import time
from typing import Any, Dict, List, Optional, Union

from edgecraftrag.base import BaseComponent, BenchType, CompType
from edgecraftrag.config_repository import (
    MilvusConfigRepository,
    MilvusDocumentRecordRepository,
)
from edgecraftrag.env import DOCUMENT_DATA_FILE, EXPERIENCE_FILE
from llama_index.core.schema import Document
from pydantic import Field, model_serializer

class Knowledge(BaseComponent):

    node_parser: Optional[BaseComponent] = Field(default=None)
    indexer: Optional[BaseComponent] = Field(default=None)
    benchmark: Optional[BaseComponent] = Field(default=None)

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        active: bool = True,
        comp_type: Optional[str] = None,
        comp_subtype: Optional[str] = None,
        experience_active: bool = False,
        idx: Optional[str] = None,
        all_document_maps: Optional[Dict] = None,
        file_paths: Optional[list] = None,
        origin_json: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(name=name, comp_type=CompType.KNOWLEDGE, **kwargs)

        self.description = description
        self.experience_active = experience_active
        self.active = active
        self.comp_type = comp_type
        self.comp_subtype = comp_subtype
        self.enable_benchmark = os.getenv("ENABLE_BENCHMARK", "False").lower() == "true"
        if idx is not None:
            self.idx = str(idx)
        if all_document_maps is not None:
            self.all_document_maps = all_document_maps
        else:
            self.all_document_maps: Dict[str, str] = {}

        self.document_records: List[Dict[str, str]] = []

        if file_paths is not None:
            self.file_paths = file_paths
            self._update_file_names()
        else:
            self.file_paths: List[str] = []
            self.file_map: Dict[str, str] = {}

        self.experience_repo = MilvusConfigRepository.create_connection("experience_data", 1)
        self.document_record_repo = MilvusDocumentRecordRepository.create_connection("document_records", 1)
        self.nodes = []
        self._origin_json = origin_json

    @property
    def get_knowledge_json(self) -> str:
        return self._origin_json

    def update_knowledge_json(self, knowledge_dict):
        origin_json = json.loads(self._origin_json)
        for k, v in knowledge_dict.items():
            if v is not None:
                origin_json[k] = v
        self._origin_json = json.dumps(origin_json)

    def _update_file_names(self) -> None:
        self.file_map = {os.path.basename(path): path for path in self.file_paths if path is not None}

    def add_file_path(
        self,
        file_path: str,
        documents: List[Document],
    ) -> bool:

        if file_path not in self.all_document_maps:
            file_id = str(uuid.uuid4())
            self.all_document_maps[file_path] = file_id
        else:
            file_id = self.all_document_maps[file_path]
        records = [
            {
                "file_id": file_id,
                "file_path": file_path,
                "doc_id": doc.id_,
                "metadata": doc.metadata,
            }
            for doc in documents
        ]
        self._add_document_records(records)

        if file_path not in self.file_paths:
            self.file_paths.append(file_path)
            self._update_file_names()

    def remove_file_path(self, file_path: str) -> List[str]:
        removed_doc_ids = []
        if file_path in self.all_document_maps:
            file_id = self.all_document_maps[file_path]
            removed_doc_ids = self._remove_document_records_by_file_id(file_id)
            del self.all_document_maps[file_path]
        if file_path in self.file_paths:
            self.file_paths.remove(file_path)
            self._update_file_names()

        return removed_doc_ids

    def get_file_paths(self) -> List[str]:
        return self.file_paths

    # Content related to experience
    def _read_experience_file(self) -> List[Dict]:
        if self.experience_repo:
            return [item["config_json"] for item in self.experience_repo.get_configs()]
        else:
            if EXPERIENCE_FILE not in self.file_paths:
                self.file_paths.append(EXPERIENCE_FILE)
            if not os.path.isfile(self.file_paths[0]):
                self.ensure_file_exists(self.file_paths[0])
            with open(self.file_paths[0], "r", encoding="utf-8") as f:
                return json.load(f)

    def _write_experience_file(self, data: List[Dict]) -> None:
        if self.experience_repo:
            return True
        else:
            with open(self.file_paths[0], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True

    def get_all_experience(self) -> List[Dict]:
        return self._read_experience_file()

    def get_experience_by_id_or_question(self, req: str) -> Optional[Dict]:
        for item in self.get_all_experience():
            if item.get("idx") == req.idx or item.get("question") == req.question:
                return item
        return None

    def add_multiple_experiences(
        self, experiences: List[Dict[str, Union[str, List[str]]]], flag: bool = True
    ) -> List[Dict]:
        result = []
        if self.experience_repo:
            for exp in experiences:
                question = exp.get("question")
                if not question:
                    raise ValueError("Each experience must have a 'question'")
                content = exp.get("content", [])
                exp_idx = exp.get("idx") or str(uuid.uuid4())

                existing = self.experience_repo.get_configs(idx=exp_idx)
                if not existing:
                    all_exps = self.get_all_experience()
                    existing = [item for item in all_exps if item.get("question") == question]
                else:
                    existing = [item["config_json"] for item in existing]

                if existing:
                    existing_item = existing[0]
                    exp_idx = existing_item.get("idx")
                    if flag:
                        existing_item["content"].extend([c for c in content if c not in existing_item["content"]])
                    else:
                        existing_item["content"] = content
                    existing_item["question"] = question
                    success = self.experience_repo.update_config_by_idx(exp_idx, existing_item)
                    if success:
                        result.append(existing_item)
                else:
                    new_item = {
                        "idx": exp_idx,
                        "question": question,
                        "content": content,
                    }
                    success = self.experience_repo.add_config_by_idx(exp_idx, new_item)
                    if success:
                        result.append(new_item)
            return result
        else:
            all_exp = self._read_experience_file()
            for exp in experiences:
                question = exp.get("question")
                if not question:
                    raise ValueError("Each experience must have a 'question'")
                content = exp.get("content", [])
                exp_idx = exp.get("idx") or str(uuid.uuid4())
                existing_idx = None
                existing_item = None
                for i, item in enumerate(all_exp):
                    if item.get("idx") == exp_idx:
                        existing_idx = i
                        existing_item = item
                        break
                if existing_idx is None:
                    for i, item in enumerate(all_exp):
                        if item.get("question") == question:
                            existing_idx = i
                            existing_item = item
                            break
                if existing_idx is not None:
                    if flag:
                        existing_item["content"].extend([c for c in content if c not in existing_item["content"]])
                        existing_item["question"] = question
                    else:
                        existing_item["content"] = content
                        existing_item["question"] = question
                    all_exp[existing_idx] = existing_item
                    result.append(existing_item)
                else:
                    new_item = {
                        "idx": exp_idx,
                        "question": question,
                        "content": content,
                    }
                    all_exp.append(new_item)
                    result.append(new_item)
            self._write_experience_file(all_exp)
            return result

    def delete_experience(self, exp_idx: str) -> bool:
        if self.experience_repo:
            return self.experience_repo.delete_config_by_idx(exp_idx)
        else:
            all_exp = self._read_experience_file()
            remaining = [item for item in all_exp if item.get("idx") != exp_idx]
            if len(remaining) != len(all_exp):
                self._write_experience_file(remaining)
                return True
            return False

    def clear_experiences(self) -> bool:
        if self.experience_repo:
            try:
                self.experience_repo.clear_all_config()
                return True
            except Exception as e:
                print(f"Clear Milvus experiences failed: {e}")
                return False
        else:
            self._write_experience_file([])
            return True

    def update_experience(self, exp_idx: str, new_question: str, new_content: List[str]) -> Optional[Dict]:
        updated_item = {
            "idx": exp_idx,
            "question": new_question,
            "content": new_content,
        }
        if self.experience_repo:
            success = self.experience_repo.update_config_by_idx(exp_idx, updated_item)
            return updated_item if success else None
        else:
            all_exp = self._read_experience_file()
            for i, item in enumerate(all_exp):
                if item.get("idx") == exp_idx:
                    all_exp[i] = updated_item
                    self._write_experience_file(all_exp)
                    return updated_item
            return None

    def add_experiences_from_file(self, file_path: str, flag: bool = False) -> List[Dict]:
        if not file_path.endswith(".json"):
            raise ValueError("File must be a JSON file")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("File content must be a list of experiences")
            experiences = []
            for item in data:
                exp = {
                    "idx": item.get("idx") or str(uuid.uuid4()),
                    "question": item.get("question", ""),
                    "content": item.get("content", []),
                }
                experiences.append(exp)

            return self.add_multiple_experiences(experiences=experiences, flag=flag)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"File error: {str(e)}")

    # Related content of document
    def _add_document_records(self, records: List[Dict[str, str]]) -> None:
        if records and self.document_record_repo:
            self.document_record_repo.save_records(records)
        elif records:
            if not os.path.isfile(DOCUMENT_DATA_FILE):
                self.ensure_file_exists(DOCUMENT_DATA_FILE)
            if os.path.exists(DOCUMENT_DATA_FILE):
                with open(DOCUMENT_DATA_FILE, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            existing_data.extend(records)
            with open(DOCUMENT_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)

    def _remove_document_records_by_file_id(self, file_id: str) -> List[Dict[str, str]]:
        deleted_records = []
        if self.document_record_repo:
            deleted_records = self.document_record_repo.delete_records_by_file_id(file_id)
        else:
            if os.path.exists(DOCUMENT_DATA_FILE):
                with open(DOCUMENT_DATA_FILE, "r", encoding="utf-8") as f:
                    all_document_data = json.load(f)
                deleted_records = [item.get("doc_id") for item in all_document_data if item.get("file_id") == file_id]
                result_documents = [item for item in all_document_data if item.get("file_id") != file_id]
                if len(deleted_records) > 0:
                    with open(DOCUMENT_DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(result_documents, f, ensure_ascii=False, indent=4)
        return deleted_records

    def clear_documents(self):
        for file_id in self.all_document_maps.values():
            self._remove_document_records_by_file_id(file_id)
        return True

    # Make sure the folder and its files exist
    def ensure_file_exists(self, file_paths):
        dir_path = os.path.dirname(file_paths)
        os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(file_paths):
            with open(file_paths, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    # Calculate the number of files or experience
    def calculate_totals(self):
        if self.comp_type == "knowledge":
            total = len(self.file_paths)
        elif self.comp_type == "experience":
            total = len(self.get_all_experience())
        else:
            total = None
        return total
    
    def update_nodes(self, nodes: List[Document]):
        self.nodes = nodes

    def add_nodes(self, nodes: List[Document]):
        self.nodes.extend(nodes)

    async def run_node_parser(self, docs: List[Document]) -> Any:
        start = 0
        if self.enable_benchmark:
            benchmark_index = self.benchmark.init_benchmark_data()
            start = time.perf_counter()
        nodes = self.node_parser.run(docs=docs)
        if self.enable_benchmark:
            benchmark_data = (
                self.benchmark.get_benchmark_data(benchmark_index, CompType.NODEPARSER) + time.perf_counter() - start
            )
            self.benchmark.update_benchmark_data(benchmark_index, CompType.NODEPARSER, benchmark_data)

            benchmark_data = self.benchmark.get_benchmark_data(benchmark_index, BenchType.CHUNK_NUM) + len(nodes)
            self.benchmark.update_benchmark_data(benchmark_index, BenchType.CHUNK_NUM, benchmark_data)
        self.add_nodes(nodes)
        return nodes
        
    async def update_nodes_to_indexer(self) -> Any:
        if self.indexer is not None:
            self.indexer.insert_nodes(self.nodes)

    async def add_nodes_to_indexer(self, nodes) -> Any:
        if self.indexer is not None:
            self.indexer.insert_nodes(nodes)

    def run(self, **kwargs) -> Any:
        pass

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "name": self.name,
            "comp_type": self.comp_type,
            "comp_subtype": self.comp_subtype,
            "node_parser": self.node_parser,
            "indexer": self.indexer,
            "file_map": self.file_map,
            "description": self.description,
            "active": self.active,
            "experience_active": self.experience_active,
            "total": self.calculate_totals(),
        }
        return set
