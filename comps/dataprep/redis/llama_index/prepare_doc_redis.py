# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

from config import EMBED_MODEL, INDEX_NAME, REDIS_URL
from fastapi import Body, File, HTTPException, UploadFile
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.redis import RedisVectorStore
from redis import Redis
from redisvl.schema import IndexSchema
from utils import *

from comps import DocPath, opea_microservices, register_microservice

upload_folder = "./uploaded_files/"


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
# llama index only support upload files now
async def ingest_documents(files: Optional[Union[UploadFile, List[UploadFile]]] = File(None)):
    print(f"files:{files}")
    if not files:
        raise HTTPException(status_code=400, detail="Please provide at least one file.")

    if not isinstance(files, list):
        files = [files]
    if not os.path.exists(upload_folder):
        Path(upload_folder).mkdir(parents=True, exist_ok=True)
    try:
        for file in files:
            save_path = upload_folder + file.filename
            await save_content_to_local_disk(save_path, file)
            await ingest_data_to_redis(DocPath(path=save_path))
            print(f"Successfully saved file {save_path}")
        return {"status": 200, "message": "Data preparation succeeded"}
    except Exception as e:
        print(f"Data preparation failed. Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Data preparation failed. Exception: {e}")


@register_microservice(
    name="opea_service@prepare_doc_redis_file", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6008
)
async def rag_get_file_structure():
    print("[ get_file_structure] ")

    if not Path(upload_folder).exists():
        print("No file uploaded, return empty list.")
        return []

    file_content = get_file_structure(upload_folder)
    return file_content


@register_microservice(
    name="opea_service@prepare_doc_redis_del", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6009
)
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - specific file path (e.g. /path/to/file.txt)
        - folder path (e.g. /path/to/folder)
        - "all": delete all files uploaded
    """
    # delete all uploaded files
    if file_path == "all":
        print("[dataprep - del] delete all files")
        remove_folder_with_ignore(upload_folder)
        print("[dataprep - del] successfully delete all files.")
        create_upload_folder(upload_folder)
        return {"status": True}

    delete_path = Path(upload_folder + "/" + encode_filename(file_path))
    print(f"[dataprep - del] delete_path: {delete_path}")

    # partially delete files/folders
    if delete_path.exists():
        # delete file
        if delete_path.is_file():
            try:
                delete_path.unlink()
            except Exception as e:
                print(f"[dataprep - del] fail to delete file {delete_path}: {e}")
                return {"status": False}
        # delete folder
        else:
            try:
                shutil.rmtree(delete_path)
            except Exception as e:
                print(f"[dataprep - del] fail to delete folder {delete_path}: {e}")
                return {"status": False}
        return {"status": True}
    else:
        raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")


if __name__ == "__main__":
    opea_microservices["opea_service@prepare_doc_redis"].start()
    opea_microservices["opea_service@prepare_doc_redis_file"].start()
    opea_microservices["opea_service@prepare_doc_redis_del"].start()
