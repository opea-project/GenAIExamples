# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Union

# from pyspark import SparkConf, SparkContext
import redis
from config import EMBED_MODEL, INDEX_NAME, KEY_INDEX_NAME, REDIS_URL
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Redis
from langchain_text_splitters import HTMLHeaderTextSplitter
from langsmith import traceable
from redis.commands.search.field import TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from comps import DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    get_file_structure,
    get_separators,
    get_tables_result,
    parse_html,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
upload_folder = "./uploaded_files/"
redis_pool = redis.ConnectionPool.from_url(REDIS_URL)


def check_index_existance(client):
    print(f"[ check index existence ] checking {client}")
    try:
        results = client.search("*")
        print(f"[ check index existence ] index of client exists: {client}")
        return results
    except Exception as e:
        print(f"[ check index existence ] index does not exist: {e}")
        return None


def create_index(client, index_name: str = KEY_INDEX_NAME):
    print(f"[ create index ] creating index {index_name}")
    try:
        definition = IndexDefinition(index_type=IndexType.HASH, prefix=["file:"])
        client.create_index((TextField("file_name"), TextField("key_ids")), definition=definition)
        print(f"[ create index ] index {index_name} successfully created")
    except Exception as e:
        print(f"[ create index ] fail to create index {index_name}: {e}")
        return False
    return True


def store_by_id(client, key, value):
    print(f"[ store by id ] storing ids of {key}")
    try:
        client.add_document(doc_id="file:" + key, file_name=key, key_ids=value)
        print(f"[ store by id ] store document success. id: file:{key}")
    except Exception as e:
        print(f"[ store by id ] fail to store document file:{key}: {e}")
        return False
    return True


def search_by_id(client, doc_id):
    print(f"[ search by id ] searching docs of {doc_id}")
    try:
        results = client.load_document(doc_id)
        print(f"[ search by id ] search success of {doc_id}")
        return results
    except Exception as e:
        print(f"[ search by id ] fail to search docs of {doc_id}: {e}")
        return None


def drop_index(index_name, redis_url=REDIS_URL):
    print(f"[ drop index ] dropping index {index_name}")
    try:
        assert Redis.drop_index(index_name=index_name, delete_documents=True, redis_url=redis_url)
        print(f"[ drop index ] index {index_name} deleted")
    except Exception as e:
        print(f"[ drop index ] index {index_name} delete failed: {e}")
        return False
    return True


def delete_by_id(client, id):
    try:
        assert client.delete_document(id)
        print(f"[ delete by id ] delete id success: {id}")
    except Exception as e:
        print(f"[ delete by id ] fail to delete ids {id}: {e}")
        return False
    return True


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
            chunk_size=doc_path.chunk_size, chunk_overlap=100, add_start_index=True, separators=get_separators()
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

    file_ids = []
    for i in range(0, num_chunks, batch_size):
        print(f"Current batch: {i}")
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        _, keys = Redis.from_texts_return_keys(
            texts=batch_texts,
            embedding=embedder,
            index_name=INDEX_NAME,
            redis_url=REDIS_URL,
        )
        print(f"keys: {keys}")
        file_ids.extend(keys)
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")

    # store file_ids into index file-keys
    r = redis.Redis(connection_pool=redis_pool)
    client = r.ft(KEY_INDEX_NAME)
    if not check_index_existance(client):
        assert create_index(client)
    file_name = doc_path.path.split("/")[-1]
    assert store_by_id(client, key=file_name, value="#".join(file_ids))

    return True


async def ingest_link_to_redis(link_list: List[str]):
    # Create embedding obj
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Create redis connection obj
    r = redis.Redis(connection_pool=redis_pool)
    client = r.ft(KEY_INDEX_NAME)

    # save link contents and doc_ids one by one
    for link in link_list:
        content = parse_html([link])[0][0]
        print(f"[ ingest link ] link: {link} content: {content}")
        encoded_link = encode_filename(link)
        save_path = upload_folder + encoded_link + ".txt"
        print(f"[ ingest link ] save_path: {save_path}")
        await save_content_to_local_disk(save_path, content)

        _, keys = Redis.from_texts_return_keys(
            texts=content,
            embedding=embedder,
            index_name=INDEX_NAME,
            redis_url=REDIS_URL,
        )
        print(f"keys: {keys}")
        if not check_index_existance(client):
            assert create_index(client)
        file_name = encoded_link + ".txt"
        assert store_by_id(client, key=file_name, value="#".join(keys))

    return True


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

        # def process_files_wrapper(files):
        #     if not isinstance(files, list):
        #         files = [files]
        #     for file in files:
        #         ingest_data_to_redis(DocPath(path=file, chunk_size=chunk_size, chunk_overlap=chunk_overlap))

        # try:
        #     # Create a SparkContext
        #     conf = SparkConf().setAppName("Parallel-dataprep").setMaster("local[*]")
        #     sc = SparkContext(conf=conf)
        #     # Create an RDD with parallel processing
        #     parallel_num = min(len(uploaded_files), os.cpu_count())
        #     rdd = sc.parallelize(uploaded_files, parallel_num)
        #     # Perform a parallel operation
        #     rdd_trans = rdd.map(process_files_wrapper)
        #     rdd_trans.collect()
        #     # Stop the SparkContext
        #     sc.stop()
        # except:
        #     # Stop the SparkContext
        #     sc.stop()

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
    print("[ dataprep - get file ] start to get file structure")

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
        assert drop_index(index_name=INDEX_NAME)
        assert drop_index(index_name=KEY_INDEX_NAME)
        print("[dataprep - del] successfully delete all files.")
        create_upload_folder(upload_folder)
        return {"status": True}

    delete_path = Path(upload_folder + "/" + encode_filename(file_path))
    print(f"[dataprep - del] delete_path: {delete_path}")

    # partially delete files/folders
    if delete_path.exists():
        r = redis.Redis(connection_pool=redis_pool)
        client = r.ft(KEY_INDEX_NAME)
        client2 = r.ft(INDEX_NAME)
        doc_id = "file:" + encode_filename(file_path)
        objs = search_by_id(client, doc_id).key_ids
        file_ids = objs.split("#")

        # delete file
        if delete_path.is_file():
            try:
                for file_id in file_ids:
                    assert delete_by_id(client2, file_id)
                assert delete_by_id(client, doc_id)
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
