# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
from typing import List, Optional, Union

from config import (
    EMBED_MODEL,
    INDEX_NAME,
    KEY_INDEX_NAME,
    OPENSEARCH_INITIAL_ADMIN_PASSWORD,
    OPENSEARCH_URL,
    SEARCH_BATCH_SIZE,
)
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_text_splitters import HTMLHeaderTextSplitter

# from pyspark import SparkConf, SparkContext
from opensearchpy import OpenSearch, helpers

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    format_search_results,
    get_separators,
    get_tables_result,
    parse_html,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

logger = CustomLogger("prepare_doc_opensearch")
logflag = os.getenv("LOGFLAG", False)

upload_folder = "./uploaded_files/"
tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
if tei_embedding_endpoint:
    # create embeddings using TEI endpoint service
    embeddings = HuggingFaceEndpointEmbeddings(model=tei_embedding_endpoint)
else:
    # create embeddings using local embedding model
    embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)
auth = ("admin", OPENSEARCH_INITIAL_ADMIN_PASSWORD)
opensearch_client = OpenSearchVectorSearch(
    opensearch_url=OPENSEARCH_URL,
    index_name=INDEX_NAME,
    embedding_function=embeddings,
    http_auth=auth,
    use_ssl=True,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)


def check_index_existence(client, index_name):
    if logflag:
        logger.info(f"[ check index existence ] checking {client}")
    try:
        exists = client.index_exists(index_name)
        exists = False if exists is None else exists
        if exists:
            if logflag:
                logger.info(f"[ check index existence ] index of client exists: {client}")
        else:
            if logflag:
                logger.info("[ check index existence ] index does not exist")
        return exists
    except Exception as e:
        if logflag:
            logger.info(f"[ check index existence ] error checking index for client: {e}")
        return False


def create_index(client, index_name: str = KEY_INDEX_NAME):
    if logflag:
        logger.info(f"[ create index ] creating index {index_name}")
    try:
        index_body = {
            "mappings": {
                "properties": {
                    "file_name": {"type": "text"},
                    "key_ids": {"type": "text"},
                }
            }
        }

        # Create the index
        client.client.indices.create(index_name, body=index_body)

        if logflag:
            logger.info(f"[ create index ] index {index_name} successfully created")
        return True
    except Exception as e:
        if logflag:
            logger.info(f"[ create index ] fail to create index {index_name}: {e}")
        return False


def store_by_id(client, key, value):
    if logflag:
        logger.info(f"[ store by id ] storing ids of {key}")
    try:
        client.client.index(
            index=KEY_INDEX_NAME, body={"file_name": f"file:${key}", "key_ids:": value}, id="file:" + key, refresh=True
        )
        if logflag:
            logger.info(f"[ store by id ] store document success. id: file:{key}")
    except Exception as e:
        if logflag:
            logger.info(f"[ store by id ] fail to store document file:{key}: {e}")
        return False
    return True


def search_by_id(client, doc_id):
    if logflag:
        logger.info(f"[ search by id ] searching docs of {doc_id}")
    try:
        result = client.client.get(index=KEY_INDEX_NAME, id=doc_id)
        if result["found"]:
            if logflag:
                logger.info(f"[ search by id ] search success of {doc_id}: {result}")
            return result
        return None
    except Exception as e:
        if logflag:
            logger.info(f"[ search by id ] fail to search docs of {doc_id}: {e}")
        return None


def drop_index(client, index_name):
    if logflag:
        logger.info(f"[ drop index ] dropping index {index_name}")
    try:
        client.client.indices.delete(index=index_name)
        if logflag:
            logger.info(f"[ drop index ] index {index_name} deleted")
    except Exception as e:
        if logflag:
            logger.info(f"[ drop index ] index {index_name} delete failed: {e}")
        return False
    return True


def delete_by_id(client, doc_id):
    try:
        response = client.client.delete(index=KEY_INDEX_NAME, id=doc_id)
        if response["result"] == "deleted":
            if logflag:
                logger.info(f"[ delete by id ] delete id success: {doc_id}")
            return True
        else:
            if logflag:
                logger.info(f"[ delete by id ] delete id failed: {doc_id}")
            return False
    except Exception as e:
        if logflag:
            logger.info(f"[ delete by id ] fail to delete ids {doc_id}: {e}")
        return False


def ingest_chunks_to_opensearch(file_name: str, chunks: List):
    if logflag:
        logger.info(f"[ ingest chunks ] file name: {file_name}")

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)

    file_ids = []
    for i in range(0, num_chunks, batch_size):
        if logflag:
            logger.info(f"[ ingest chunks ] Current batch: {i}")
        batch_chunks = chunks[i : i + batch_size]

        keys = opensearch_client.add_texts(texts=batch_chunks, metadatas=[{"source": file_name} for _ in batch_chunks])
        if logflag:
            logger.info(f"[ ingest chunks ] keys: {keys}")
        file_ids.extend(keys)
        if logflag:
            logger.info(f"[ ingest chunks ] Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")

    # store file_ids into index file-keys
    if not check_index_existence(opensearch_client, KEY_INDEX_NAME):
        assert create_index(opensearch_client)

    try:
        assert store_by_id(opensearch_client, key=file_name, value="#".join(file_ids))
    except Exception as e:
        if logflag:
            logger.info(f"[ ingest chunks ] {e}. Fail to store chunks of file {file_name}.")
        raise HTTPException(status_code=500, detail=f"Fail to store chunks of file {file_name}.")
    return True


def ingest_data_to_opensearch(doc_path: DocPath):
    """Ingest document to OpenSearch."""
    path = doc_path.path
    if logflag:
        logger.info(f"[ ingest data ] Parsing document {path}.")

    if path.endswith(".html"):
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=doc_path.chunk_size,
            chunk_overlap=doc_path.chunk_overlap,
            add_start_index=True,
            separators=get_separators(),
        )

    content = document_loader(path)
    if logflag:
        logger.info("[ ingest data ] file content loaded")

    structured_types = [".xlsx", ".csv", ".json", "jsonl"]
    _, ext = os.path.splitext(path)

    if ext in structured_types:
        chunks = content
    else:
        chunks = text_splitter.split_text(content)

    ### Specially processing for the table content in PDFs
    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)
        chunks = chunks + table_chunks
    if logflag:
        logger.info(f"[ ingest data ] Done preprocessing. Created {len(chunks)} chunks of the given file.")

    file_name = doc_path.path.split("/")[-1]
    return ingest_chunks_to_opensearch(file_name, chunks)


def search_all_documents(index_name, offset, search_batch_size):
    try:
        response = opensearch_client.client.search(
            index=index_name,
            body={
                "query": {"match_all": {}},
                "from": offset,  # Starting position
                "size": search_batch_size,  # Number of results to return
            },
        )
        # Get total number of matching documents
        total_hits = response["hits"]["total"]["value"]
        # Get the documents from the current batch
        documents = response["hits"]["hits"]

        return {"total_hits": total_hits, "documents": documents}

    except Exception as e:
        print(f"Error performing search: {e}")
        return None


@register_microservice(name="opea_service@prepare_doc_opensearch", endpoint="/v1/dataprep", host="0.0.0.0", port=6007)
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1500),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    if logflag:
        logger.info(f"[ upload ] files:{files}")
        logger.info(f"[ upload ] link_list:{link_list}")

    if files:
        if not isinstance(files, list):
            files = [files]
        uploaded_files = []

        for file in files:
            encode_file = encode_filename(file.filename)
            doc_id = "file:" + encode_file
            if logflag:
                logger.info(f"[ upload ] processing file {doc_id}")

            # check whether the file already exists
            key_ids = None
            try:
                document = search_by_id(opensearch_client, doc_id)
                if document:
                    if logflag:
                        logger.info(f"[ upload ] File {file.filename} already exists.")
                    key_ids = document["_id"]
            except Exception as e:
                logger.info(f"[ upload ] File {file.filename} does not exist.")
            if key_ids:
                raise HTTPException(
                    status_code=400, detail=f"Uploaded file {file.filename} already exists. Please change file name."
                )

            save_path = upload_folder + encode_file
            await save_content_to_local_disk(save_path, file)
            ingest_data_to_opensearch(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                )
            )
            uploaded_files.append(save_path)
            if logflag:
                logger.info(f"[ upload ] Successfully saved file {save_path}")

        result = {"status": 200, "message": "Data preparation succeeded"}
        if logflag:
            logger.info(result)
        return result

    if link_list:
        link_list = json.loads(link_list)  # Parse JSON string to list
        if not isinstance(link_list, list):
            raise HTTPException(status_code=400, detail=f"Link_list {link_list} should be a list.")
        for link in link_list:
            encoded_link = encode_filename(link)
            doc_id = "file:" + encoded_link + ".txt"
            if logflag:
                logger.info(f"[ upload ] processing link {doc_id}")

            # check whether the link file already exists
            key_ids = None
            try:
                document = search_by_id(opensearch_client, doc_id)
                if document:
                    if logflag:
                        logger.info(f"[ upload ] Link {link} already exists.")
                    key_ids = document["_id"]
            except Exception as e:
                logger.info(f"[ upload ] Link {link} does not exist. Keep storing.")
            if key_ids:
                raise HTTPException(
                    status_code=400, detail=f"Uploaded link {link} already exists. Please change another link."
                )

            save_path = upload_folder + encoded_link + ".txt"
            content = parse_html([link])[0][0]
            await save_content_to_local_disk(save_path, content)
            ingest_data_to_opensearch(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                )
            )
        if logflag:
            logger.info(f"[ upload ] Successfully saved link list {link_list}")
        return {"status": 200, "message": "Data preparation succeeded"}

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_opensearch", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6007
)
async def rag_get_file_structure():
    if logflag:
        logger.info("[ get ] start to get file structure")

    offset = 0
    file_list = []

    # check index existence
    res = check_index_existence(opensearch_client, KEY_INDEX_NAME)
    if not res:
        if logflag:
            logger.info(f"[ get ] index {KEY_INDEX_NAME} does not exist")
        return file_list

    while True:
        response = search_all_documents(KEY_INDEX_NAME, offset, SEARCH_BATCH_SIZE)
        # no doc retrieved
        if len(response) < 2:
            break

        def format_opensearch_results(response, file_list):
            for document in response["documents"]:
                file_id = document["_id"]
                file_list.append({"name": file_id, "id": file_id, "type": "File", "parent": ""})

        file_list = format_opensearch_results(response, file_list)
        offset += SEARCH_BATCH_SIZE
        # last batch
        if (len(response) - 1) // 2 < SEARCH_BATCH_SIZE:
            break
    if logflag:
        logger.info(f"[get] final file_list: {file_list}")
    return file_list


@register_microservice(
    name="opea_service@prepare_doc_opensearch", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6007
)
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - specific file path (e.g. /path/to/file.txt)
        - "all": delete all files uploaded
    """

    # delete all uploaded files
    if file_path == "all":
        if logflag:
            logger.info("[ delete ] delete all files")

        # drop index KEY_INDEX_NAME
        if check_index_existence(opensearch_client, KEY_INDEX_NAME):
            try:
                assert drop_index(index_name=KEY_INDEX_NAME)
            except Exception as e:
                if logflag:
                    logger.info(f"[ delete ] {e}. Fail to drop index {KEY_INDEX_NAME}.")
                raise HTTPException(status_code=500, detail=f"Fail to drop index {KEY_INDEX_NAME}.")
        else:
            logger.info(f"[ delete ] Index {KEY_INDEX_NAME} does not exits.")

        # drop index INDEX_NAME
        if check_index_existence(opensearch_client, INDEX_NAME):
            try:
                assert drop_index(index_name=INDEX_NAME)
            except Exception as e:
                if logflag:
                    logger.info(f"[ delete ] {e}. Fail to drop index {INDEX_NAME}.")
                raise HTTPException(status_code=500, detail=f"Fail to drop index {INDEX_NAME}.")
        else:
            if logflag:
                logger.info(f"[ delete ] Index {INDEX_NAME} does not exits.")

        # delete files on local disk
        try:
            remove_folder_with_ignore(upload_folder)
        except Exception as e:
            if logflag:
                logger.info(f"[ delete ] {e}. Fail to delete {upload_folder}.")
            raise HTTPException(status_code=500, detail=f"Fail to delete {upload_folder}.")

        if logflag:
            logger.info("[ delete ] successfully delete all files.")
        create_upload_folder(upload_folder)
        if logflag:
            logger.info({"status": True})
        return {"status": True}
    else:
        raise HTTPException(status_code=404, detail="Single file deletion is not implemented yet")


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    opea_microservices["opea_service@prepare_doc_opensearch"].start()
