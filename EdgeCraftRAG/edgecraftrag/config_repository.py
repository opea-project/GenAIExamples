# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import time
from typing import Dict, List, Optional

from edgecraftrag.env import AGENT_FILE, KNOWLEDGEBASE_FILE, PIPELINE_FILE
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)


class MilvusConfigRepository:
    def __init__(
        self,
        Repo_config_name: Optional[str] = "pipeline_config",
        vector_url: Optional[str] = None,
    ):
        self.vector_url = vector_url or os.getenv("METADATA_DATABASE_URL")
        self.host, self.port = None, None
        if self.vector_url:
            host_port = self.vector_url.replace("http://", "").replace("https://", "")
            if ":" in host_port:
                self.host, self.port = host_port.split(":", 1)
        self.collection_name = Repo_config_name
        self.alias = Repo_config_name
        self.collection = None
        self.connected = False

    def _connect(self) -> None:
        try:
            connections.connect(host=self.host, port=self.port, alias=self.alias)
        except Exception as e:
            raise RuntimeError(f"Connect Milvus failed: {str(e)}")

    def _init_collection(self) -> Collection:
        if not utility.has_collection(self.collection_name, using=self.alias):
            fields = [
                FieldSchema(
                    name="idx",
                    dtype=DataType.VARCHAR,
                    max_length=100,
                    is_primary=True,
                    auto_id=False,
                ),
                FieldSchema(name="config_json", dtype=DataType.JSON),
                FieldSchema(name="dummy_vector", dtype=DataType.FLOAT_VECTOR, dim=2),
            ]
            schema = CollectionSchema(fields, description="Config storage (idx as primary key)")
            collection = Collection(self.collection_name, schema, using=self.alias)
            collection.create_index("dummy_vector", {"index_type": "FLAT", "metric_type": "L2"})
            return collection
        return Collection(self.collection_name, using=self.alias)

    @classmethod
    def create_connection(
        cls,
        Repo_config_name: Optional[str] = "pipeline_config",
        max_retries: Optional[int] = 10,
        vector_url: Optional[str] = None,
    ):
        instance = cls(Repo_config_name, vector_url)
        retry_interval = 6
        if instance.host:
            for retry in range(max_retries):
                try:
                    instance._connect()
                    instance.collection = instance._init_collection()
                    instance.collection.load()
                    instance.connected = True
                    return instance
                except Exception as e:
                    print(f"Attempt {retry + 1} failed: {str(e)}")
                    if retry < max_retries - 1:
                        time.sleep(retry_interval)
            raise ConnectionError(f"Max retries ({max_retries}) reached")
        return None

    def save_configs(self, configs: List[Dict]) -> None:
        self.collection.delete("idx != ''")
        insert_data = []
        for config in configs:
            insert_data.append(
                {
                    "idx": config["idx"],
                    "config_json": config,
                    "dummy_vector": [0.0, 0.0],
                }
            )
        if insert_data:
            idx_list = [i["idx"] for i in insert_data]
            configs_list = [i["config_json"] for i in insert_data]
            vectors = [i["dummy_vector"] for i in insert_data]
            self.collection.insert([idx_list, configs_list, vectors])
            self.collection.flush()
        else:
            print("No data to insert")

    def get_configs(self, idx: Optional[str] = None, output_fields: Optional[list] = None) -> List[Dict]:
        try:
            self.collection.load()
            output_fields = output_fields or ["idx", "config_json"]
            if idx:
                expr = f'idx == "{idx}"'
            else:
                expr = "idx != ''"
            results = self.collection.query(expr=expr, output_fields=output_fields)
            return results
        except Exception as e:
            print(f"Read error: {e}")
            return []

    def add_config_by_idx(self, idx: str, config_json: Dict) -> bool:
        if not self.connected or not self.collection:
            raise RuntimeError("Not connected to Milvus")
        try:
            self.collection.load()
            self.collection.insert([[idx], [config_json], [[0.0, 0.0]]])
            return True
        except Exception as e:
            print(f"Add failed: {e}")
            return False

    def delete_config_by_idx(self, idx: str) -> int:
        if not self.connected or not self.collection:
            raise RuntimeError("Not connected to Milvus")
        try:
            self.collection.load()
            res = self.collection.delete(f'idx == "{idx}"')
            self.collection.flush()
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return 0

    def update_config_by_idx(self, idx: str, new_config_json: Dict) -> bool:
        if not self.connected or not self.collection:
            raise RuntimeError("Not connected to Milvus")
        try:
            self.collection.load()
            upsert_data = [[idx], [new_config_json], [[0.0, 0.0]]]
            self.collection.upsert(upsert_data)
            return True
        except Exception as e:
            print(f"Upsert failed: {str(e)}")
            return False

    def clear_all_config(self):
        try:
            self.collection.load()
            res = self.collection.delete("idx != ''")
            self.collection.flush()
            return True
        except Exception as e:
            print(f"Clear all configs failed: {e}")
            return False


class MilvusDocumentRecordRepository:
    def __init__(
        self,
        repo_name: Optional[str] = "document_records",
        vector_url: Optional[str] = None,
    ):
        if vector_url:
            self.vector_url = vector_url
        else:
            self.vector_url = os.getenv("METADATA_DATABASE_URL")
        self.host, self.port = None, None
        if self.vector_url:
            if self.vector_url.startswith(("http://", "https://")):
                host_port = self.vector_url.replace("http://", "").replace("https://", "")
            else:
                host_port = self.vector_url
            if ":" in host_port:
                self.host, self.port = host_port.split(":", 1)

        self.collection_name = repo_name
        self.alias = repo_name
        self.collection = None
        self.connected = False

    def _connect(self) -> None:
        try:
            connections.connect(host=self.host, port=self.port, alias=self.alias)
        except Exception as e:
            raise RuntimeError(f"Unable to connect to Milvus server: {str(e)}")

    def _init_collection(self) -> Collection:
        if not utility.has_collection(self.collection_name, using=self.alias):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="dummy_vector", dtype=DataType.FLOAT_VECTOR, dim=2),
            ]
            schema = CollectionSchema(fields, description="File-Document association records (with metadata)")
            collection = Collection(name=self.collection_name, schema=schema, using=self.alias)
            index_params = {"index_type": "FLAT", "metric_type": "L2"}
            collection.create_index(field_name="dummy_vector", index_params=index_params)
            return collection
        else:
            return Collection(self.collection_name, using=self.alias)

    @classmethod
    def create_connection(
        cls,
        repo_name: Optional[str] = "document_records",
        max_retries: Optional[int] = 10,
        vector_url: Optional[str] = None,
    ):
        instance = cls(repo_name, vector_url)
        retry_interval = 6
        if instance.host:
            for retry in range(max_retries):
                try:
                    instance._connect()
                    instance.collection = instance._init_collection()
                    instance.collection.load()
                    instance.connected = True
                    return instance
                except Exception as e:
                    print(f"Attempt {retry + 1} failed: {str(e)}")
                    if retry < max_retries - 1:
                        print(f"Retrying in {retry_interval}s...")
                        time.sleep(retry_interval)
            raise ConnectionError(f"Max retries ({max_retries}) reached. Failed to connect to Milvus")
        else:
            return None

    def save_records(self, records: List[Dict[str, str]]) -> None:
        if not records:
            print("No records to save")
            return
        insert_data = [
            [rec["file_id"] for rec in records],
            [rec["file_path"] for rec in records],
            [rec["doc_id"] for rec in records],
            [rec.get("metadata", {}) for rec in records],
            [[0.0, 0.0] for _ in records],
        ]
        self.collection.insert(insert_data)

    def delete_records_by_file_id(self, file_id: str) -> List[str]:
        expr = f'file_id == "{file_id}"'
        results = self.collection.query(expr=expr, output_fields=["doc_id"])
        deleted_doc_ids = [res["doc_id"] for res in results]

        if deleted_doc_ids:
            self.collection.delete(expr=expr)
        return deleted_doc_ids

    def get_records_by_file_id(self, file_id: str) -> List[Dict]:
        expr = f'file_id == "{file_id}"'
        results = self.collection.query(
            expr=expr,
            output_fields=["id", "file_id", "file_path", "doc_id", "metadata"],
        )
        return results


# Configuration of the persistence pipeline
pipeline_milvus_repo = MilvusConfigRepository.create_connection("pipeline_config", 20)


async def save_pipeline_configurations(operation: str = None, pipeline=None):
    try:
        json_str = pipeline.get_pipeline_json
        target_data = json.loads(json_str)
        target_data["idx"] = pipeline.idx
        target_idx = target_data.get("idx")
        if "generator" in target_data and operation != "delete":
            target_data["generator"]["prompt_content"] = pipeline.generator.prompt_content
            target_data["documents_cache"] = pipeline.documents_cache
            target_data["active"] = pipeline.status.active

        if pipeline_milvus_repo:
            if operation == "add":
                success = pipeline_milvus_repo.add_config_by_idx(target_idx, target_data)
            elif operation == "delete":
                success = pipeline_milvus_repo.delete_config_by_idx(target_idx)
            elif operation == "update":
                success = pipeline_milvus_repo.update_config_by_idx(target_idx, target_data)
            if not success:
                return False
            return True
        else:
            existing_pipelines = []
            if os.path.exists(PIPELINE_FILE):
                with open(PIPELINE_FILE, "r", encoding="utf-8") as f:
                    existing_pipelines = json.load(f)
                if not isinstance(existing_pipelines, list):
                    existing_pipelines = []

            if operation == "add":
                if any(p.get("idx") == target_idx for p in existing_pipelines):
                    return {"message": "Pipeline already exists"}
                existing_pipelines.append(target_data)
            elif operation == "delete":
                existing_pipelines = [p for p in existing_pipelines if p.get("idx") != target_idx]
            elif operation == "update":
                for i in range(len(existing_pipelines)):
                    if existing_pipelines[i].get("idx") == target_idx:
                        existing_pipelines[i] = target_data
            else:
                return {"message": f"Invalid operation: {operation}"}
            with open(PIPELINE_FILE, "w", encoding="utf-8") as f:
                json.dump(existing_pipelines, f, indent=2, ensure_ascii=False)
            return True
    except Exception as e:
        print(f"Error saving pipelines: {e}")


# Configuration of knowledge base for persistence
knowledgebase_config_repo = MilvusConfigRepository.create_connection("knowledgebase_config", 1)


async def save_knowledge_configurations(operation: str = None, kb=None):
    try:
        if not kb:
            return {"message": "Missing knowledgebase data"}
        target_kb = {
            "idx": kb.idx,
            "name": kb.name,
            "description": kb.description,
            "active": kb.active,
            "file_paths": kb.file_paths,
            "comp_type": kb.comp_type,
            "comp_subtype": kb.comp_subtype,
            "experience_active": kb.experience_active,
            "all_document_maps": kb.all_document_maps,
        }
        target_idx = target_kb.get("idx")
        if not target_idx:
            return {"message": "Missing 'idx' in knowledgebase data"}

        if knowledgebase_config_repo:
            if operation == "add":
                success = knowledgebase_config_repo.add_config_by_idx(target_idx, target_kb)
            elif operation == "delete":
                success = knowledgebase_config_repo.delete_config_by_idx(target_idx)
            elif operation == "update":
                success = knowledgebase_config_repo.update_config_by_idx(target_idx, target_kb)
            else:
                return {"message": f"Invalid operation: {operation}"}
            return success
        else:
            existing_kbs = []
            if os.path.exists(KNOWLEDGEBASE_FILE):
                with open(KNOWLEDGEBASE_FILE, "r", encoding="utf-8") as f:
                    existing_kbs = json.load(f)
                if not isinstance(existing_kbs, list):
                    existing_kbs = []
            if operation == "add":
                existing_kbs.append(target_kb)
            elif operation == "delete":
                existing_kbs = [item for item in existing_kbs if item.get("idx") != target_idx]
            elif operation == "update":
                for i in range(len(existing_kbs)):
                    if existing_kbs[i].get("idx") == target_idx:
                        existing_kbs[i] = target_kb
            else:
                return {"message": f"Invalid operation: {operation}"}
            with open(KNOWLEDGEBASE_FILE, "w", encoding="utf-8") as f:
                json.dump(existing_kbs, f, indent=2, ensure_ascii=False)
            return True
    except Exception as e:
        print(f"Error saving Knowledge base: {e}")


# Configuration of the persistence agent
agent_milvus_repo = MilvusConfigRepository.create_connection("agent_config", 1)


async def save_agent_configurations(operation: str = None, agents=None):
    try:
        if agent_milvus_repo:
            if not agents:
                return False
            for agent in agents.values():
                target_data = agent.model_dump(mode="json")
                if operation == "delete":
                    success = agent_milvus_repo.delete_config_by_idx(agent.idx)
                    if not success:
                        return False
                    continue

                target_idx = target_data.get("idx")
                if not target_idx:
                    return {"message": "Missing 'idx' in data"}

                if operation == "add":
                    success = agent_milvus_repo.add_config_by_idx(target_idx, target_data)

                elif operation == "update":
                    success = agent_milvus_repo.update_config_by_idx(target_idx, target_data)

                if not success:
                    return False
            return True
        else:
            if not agents:
                return False
            agent_list = []
            for agent in agents.values():
                agent_list.append(agent.model_dump(mode="json"))
            json_str = json.dumps(agent_list, indent=2, ensure_ascii=False)
            with open(AGENT_FILE, "w", encoding="utf-8") as f:
                f.write(json_str)
    except Exception as e:
        print(f"Error saving agents: {e}")
