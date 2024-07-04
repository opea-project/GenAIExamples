# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Union

from config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, REDIS_URL
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Redis
from langchain_text_splitters import HTMLHeaderTextSplitter
from langsmith import traceable
from pyspark import SparkConf, SparkContext

from comps import DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    get_file_structure,
    get_tables_result,
    parse_html,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
upload_folder = "./uploaded_files/"


def ingest_data_to_redis(doc_path: DocPath):
    """Ingest document to Redis."""
    path = doc_path.path
    print(f"Parsing document {path}.")

    if path.endswith(".html"):
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=doc_path.chunk_size, chunk_overlap=100, add_start_index=True
        )

    content = document_loader(path)

    chunks = text_splitter.split_text(content)
    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)
        chunks = chunks + table_chunks
    print("Done preprocessing. Created ", len(chunks), " chunks of the original pdf")

    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        _ = Redis.from_texts(
            texts=batch_texts,
            embedding=embedder,
            index_name=INDEX_NAME,
            index_schema=INDEX_SCHEMA,
            redis_url=REDIS_URL,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")
    return True


async def ingest_link_to_redis(link_list: List[str]):
    data_collection = parse_html(link_list)

    for content, link in data_collection:
        print(f"[ ingest link ] link: {link} content: {content}")
        encoded_link = encode_filename(link)
        save_path = upload_folder + encoded_link + ".txt"
        print(f"[ ingest link ] save_path: {save_path}")
        await save_content_to_local_disk(save_path, content)

    texts = []
    metadatas = []
    for data, meta in data_collection:
        doc_id = str(uuid.uuid4())
        metadata = {"source": meta, "identify_id": doc_id}
        texts.append(data)
        metadatas.append(metadata)

    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    _ = Redis.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embedder,
        index_name=INDEX_NAME,
        redis_url=REDIS_URL,
        index_schema=INDEX_SCHEMA,
    )


@register_microservice(name="opea_service@prepare_doc_redis", endpoint="/v1/dataprep", host="0.0.0.0", port=6007)
@traceable(run_type="tool")
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1500),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    print(f"files:{files}")
    print(f"link_list:{link_list}")

    if files:
        if not isinstance(files, list):
            files = [files]
        uploaded_files = []
        for file in files:
            encode_file = encode_filename(file.filename)
            save_path = upload_folder + encode_file
            await save_content_to_local_disk(save_path, file)
            ingest_data_to_redis(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                )
            )
            uploaded_files.append(save_path)
            print(f"Successfully saved file {save_path}")

        def process_files_wrapper(files):
            if not isinstance(files, list):
                files = [files]
            for file in files:
                ingest_data_to_redis(DocPath(path=file, chunk_size=chunk_size, chunk_overlap=chunk_overlap))

        try:
            # Create a SparkContext
            conf = SparkConf().setAppName("Parallel-dataprep").setMaster("local[*]")
            sc = SparkContext(conf=conf)
            # Create an RDD with parallel processing
            parallel_num = min(len(uploaded_files), os.cpu_count())
            rdd = sc.parallelize(uploaded_files, parallel_num)
            # Perform a parallel operation
            rdd_trans = rdd.map(process_files_wrapper)
            rdd_trans.collect()
            # Stop the SparkContext
            sc.stop()
        except:
            # Stop the SparkContext
            sc.stop()
        return {"status": 200, "message": "Data preparation succeeded"}

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail="link_list should be a list.")
            await ingest_link_to_redis(link_list)
            print(f"Successfully saved link list {link_list}")
            return {"status": 200, "message": "Data preparation succeeded"}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_redis_file", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6008
)
@traceable(run_type="tool")
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
@traceable(run_type="tool")
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
    create_upload_folder(upload_folder)
    opea_microservices["opea_service@prepare_doc_redis"].start()
    opea_microservices["opea_service@prepare_doc_redis_file"].start()
    opea_microservices["opea_service@prepare_doc_redis_del"].start()
