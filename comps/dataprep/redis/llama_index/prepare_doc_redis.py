# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
from typing import List, Optional, Union

from config import EMBED_MODEL, INDEX_NAME, REDIS_URL
from fastapi import File, Form, HTTPException, UploadFile
from langsmith import traceable
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.redis import RedisVectorStore
from redis import Redis
from redisvl.schema import IndexSchema

from comps import DocPath, opea_microservices, register_microservice


async def save_file_to_local_disk(save_path: str, file):
    save_path = Path(save_path)
    with save_path.open("wb") as fout:
        try:
            content = await file.read()
            fout.write(content)
        except Exception as e:
            print(f"Write file failed. Exception: {e}")
            raise HTTPException(status_code=500, detail=f"Write file {save_path} failed. Exception: {e}")


async def ingest_data_to_redis(doc_path: DocPath):
    embedder = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    print(f"embedder: {embedder}")
    Settings.embed_model = embedder
    doc_path = doc_path.path
    content = SimpleDirectoryReader(input_files=[doc_path]).load_data()
    redis_client = Redis.from_url(REDIS_URL)
    schema = IndexSchema.from_dict(
        {
            "index": {"name": INDEX_NAME, "prefix": f"doc:{INDEX_NAME}"},
            "fields": [
                {"name": "id", "type": "tag"},
                {"name": "doc_id", "type": "tag"},
                {"name": "text", "type": "text"},
                {"name": "content", "type": "text"},
                {"name": "source", "type": "text"},
                {"name": "start_index", "type": "numeric"},
                {
                    "name": "vector",
                    "type": "vector",
                    "attrs": {"dims": 768, "algorithm": "HNSW", "date_type": "FLOAT32"},
                },
            ],
        }
    )
    vector_store = RedisVectorStore(redis_client=redis_client, schema=schema)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    _ = VectorStoreIndex.from_documents(content, storage_context=storage_context)
    print("[ ingest data ] data ingested into Redis DB.")
    return True


@register_microservice(name="opea_service@prepare_doc_redis", endpoint="/v1/dataprep", host="0.0.0.0", port=6007)
@traceable(run_type="tool")
# llama index only support upload files now
async def ingest_documents(files: Optional[Union[UploadFile, List[UploadFile]]] = File(None)):
    print(f"files:{files}")
    if not files:
        raise HTTPException(status_code=400, detail="Please provide at least one file.")

    if not isinstance(files, list):
        files = [files]
    upload_folder = "./uploaded_files/"
    if not os.path.exists(upload_folder):
        Path(upload_folder).mkdir(parents=True, exist_ok=True)
    try:
        for file in files:
            save_path = upload_folder + file.filename
            await save_file_to_local_disk(save_path, file)
            await ingest_data_to_redis(DocPath(path=save_path))
            print(f"Successfully saved file {save_path}")
        return {"status": 200, "message": "Data preparation succeeded"}
    except Exception as e:
        print(f"Data preparation failed. Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Data preparation failed. Exception: {e}")


if __name__ == "__main__":
    opea_microservices["opea_service@prepare_doc_redis"].start()
