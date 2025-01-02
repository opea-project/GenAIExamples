# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
from typing import List, Optional, Union

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBED_MODEL,
    ES_CONNECTION_STRING,
    INDEX_NAME,
    LOG_FLAG,
    TEI_ENDPOINT,
    UPLOADED_FILES_PATH,
)
from elasticsearch import Elasticsearch
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_core.documents import Document
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.src.utils import (
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

logger = CustomLogger(__name__)


def create_index() -> None:
    if not es_client.indices.exists(index=INDEX_NAME):
        es_client.indices.create(index=INDEX_NAME)


def get_embedder() -> Union[HuggingFaceEndpointEmbeddings, HuggingFaceBgeEmbeddings]:
    """Obtain required Embedder."""

    if TEI_ENDPOINT:
        return HuggingFaceEndpointEmbeddings(model=TEI_ENDPOINT)
    else:
        return HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)


def get_elastic_store(embedder: Union[HuggingFaceEndpointEmbeddings, HuggingFaceBgeEmbeddings]) -> ElasticsearchStore:
    """Get Elasticsearch vector store."""

    return ElasticsearchStore(index_name=INDEX_NAME, embedding=embedder, es_connection=es_client)


def delete_embeddings(doc_name: str) -> bool:
    """Delete documents from Elasticsearch."""

    try:
        if doc_name == "all":
            if LOG_FLAG:
                logger.info("Deleting all documents from vectorstore")

            query = {"query": {"match_all": {}}}
        else:
            if LOG_FLAG:
                logger.info(f"Deleting {doc_name} from vectorstore")

            query = {"query": {"match": {"metadata.doc_name": {"query": doc_name, "operator": "AND"}}}}

        es_client.delete_by_query(index=INDEX_NAME, body=query)

        return True

    except Exception as e:
        if LOG_FLAG:
            logger.info(f"An unexpected error occurred: {e}")

        return False


def search_by_filename(file_name: str) -> bool:
    """Search Elasticsearch by file name."""

    query = {"query": {"match": {"metadata.doc_name": {"query": file_name, "operator": "AND"}}}}
    results = es_client.search(index=INDEX_NAME, body=query)

    if LOG_FLAG:
        logger.info(f"[ search by file ] searched by {file_name}")
        logger.info(f"[ search by file ] {len(results['hits'])} results: {results}")

    return results["hits"]["total"]["value"] > 0


def ingest_doc_to_elastic(doc_path: DocPath) -> None:
    """Ingest documents to Elasticsearch."""

    path = doc_path.path
    file_name = path.split("/")[-1]
    if LOG_FLAG:
        logger.info(f"Parsing document {path}, file name: {file_name}.")

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

    structured_types = [".xlsx", ".csv", ".json", "jsonl"]
    _, ext = os.path.splitext(path)

    if ext in structured_types:
        chunks = content
    else:
        chunks = text_splitter.split_text(content)

    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)
        chunks = chunks + table_chunks

    if LOG_FLAG:
        logger.info(f"Done preprocessing. Created {len(chunks)} chunks of the original file.")

    batch_size = 32
    num_chunks = len(chunks)

    metadata = dict({"doc_name": str(file_name)})

    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        documents = [Document(page_content=text, metadata=metadata) for text in batch_texts]
        _ = es_store.add_documents(documents=documents)
        if LOG_FLAG:
            logger.info(f"Processed batch {i // batch_size + 1}/{(num_chunks - 1) // batch_size + 1}")


async def ingest_link_to_elastic(link_list: List[str]) -> None:
    """Ingest data scraped from website links into Elasticsearch."""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=get_separators(),
    )

    batch_size = 32

    for link in link_list:
        content = parse_html([link])[0][0]
        if LOG_FLAG:
            logger.info(f"[ ingest link ] link: {link} content: {content}")

        encoded_link = encode_filename(link)
        save_path = UPLOADED_FILES_PATH + encoded_link + ".txt"
        doc_path = UPLOADED_FILES_PATH + link + ".txt"
        if LOG_FLAG:
            logger.info(f"[ ingest link ] save_path: {save_path}")

        await save_content_to_local_disk(save_path, content)

        chunks = text_splitter.split_text(content)

        num_chunks = len(chunks)
        metadata = [dict({"doc_name": str(doc_path)})]

        for i in range(0, num_chunks, batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_texts = batch_chunks

            documents = [Document(page_content=text, metadata=metadata) for text in batch_texts]
            _ = es_store.add_documents(documents=documents)

            if LOG_FLAG:
                logger.info(f"Processed batch {i // batch_size + 1}/{(num_chunks - 1) // batch_size + 1}")


@register_microservice(name="opea_service@prepare_doc_elastic", endpoint="/v1/dataprep", host="0.0.0.0", port=6011)
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1500),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    """Ingest documents for RAG."""

    if LOG_FLAG:
        logger.info(f"files:{files}")
        logger.info(f"link_list:{link_list}")

    if files and link_list:
        raise HTTPException(status_code=400, detail="Provide either a file or a string list, not both.")

    if files:
        if not isinstance(files, list):
            files = [files]

        if not os.path.exists(UPLOADED_FILES_PATH):
            Path(UPLOADED_FILES_PATH).mkdir(parents=True, exist_ok=True)

        for file in files:
            encode_file = encode_filename(file.filename)
            save_path = UPLOADED_FILES_PATH + encode_file
            filename = save_path.split("/")[-1]

            try:
                exists = search_by_filename(filename)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed when searching in Elasticsearch for file {file.filename}.",
                )

            if exists:
                if LOG_FLAG:
                    logger.info(f"[ upload ] File {file.filename} already exists.")

                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded file {file.filename} already exists. Please change file name.",
                )

            await save_content_to_local_disk(save_path, file)

            ingest_doc_to_elastic(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                )
            )
            if LOG_FLAG:
                logger.info(f"Successfully saved file {save_path}")

        result = {"status": 200, "message": "Data preparation succeeded"}

        if LOG_FLAG:
            logger.info(result)
        return result

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail="link_list should be a list.")

            await ingest_link_to_elastic(link_list)

            if LOG_FLAG:
                logger.info(f"Successfully saved link list {link_list}")

            result = {"status": 200, "message": "Data preparation succeeded"}

            if LOG_FLAG:
                logger.info(result)
            return result

        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_elastic",
    endpoint="/v1/dataprep/get_file",
    host="0.0.0.0",
    port=6011,
)
async def rag_get_file_structure():
    """Obtain uploaded file list."""

    if LOG_FLAG:
        logger.info("[ dataprep - get file ] start to get file structure")

    if not Path(UPLOADED_FILES_PATH).exists():
        if LOG_FLAG:
            logger.info("No file uploaded, return empty list.")
        return []

    file_content = get_file_structure(UPLOADED_FILES_PATH)

    if LOG_FLAG:
        logger.info(file_content)

    return file_content


@register_microservice(
    name="opea_service@prepare_doc_elastic",
    endpoint="/v1/dataprep/delete_file",
    host="0.0.0.0",
    port=6011,
)
async def delete_single_file(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - specific file path (e.g. /path/to/file.txt)
        - folder path (e.g. /path/to/folder)
        - "all": delete all files uploaded
    """
    if file_path == "all":
        if LOG_FLAG:
            logger.info("[dataprep - del] delete all files")
        remove_folder_with_ignore(UPLOADED_FILES_PATH)
        assert delete_embeddings(file_path)
        if LOG_FLAG:
            logger.info("[dataprep - del] successfully delete all files.")
        create_upload_folder(UPLOADED_FILES_PATH)
        if LOG_FLAG:
            logger.info({"status": True})
        return {"status": True}

    delete_path = Path(UPLOADED_FILES_PATH + "/" + encode_filename(file_path))

    if LOG_FLAG:
        logger.info(f"[dataprep - del] delete_path: {delete_path}")

    if delete_path.exists():
        # delete file
        if delete_path.is_file():
            try:
                assert delete_embeddings(file_path)
                delete_path.unlink()
            except Exception as e:
                if LOG_FLAG:
                    logger.info(f"[dataprep - del] fail to delete file {delete_path}: {e}")
                    logger.info({"status": False})
                return {"status": False}
        # delete folder
        else:
            if LOG_FLAG:
                logger.info("[dataprep - del] delete folder is not supported for now.")
                logger.info({"status": False})
            return {"status": False}
        if LOG_FLAG:
            logger.info({"status": True})
        return {"status": True}
    else:
        raise HTTPException(status_code=404, detail="File/folder not found. Please check del_path.")


if __name__ == "__main__":
    es_client = Elasticsearch(hosts=ES_CONNECTION_STRING)
    es_store = get_elastic_store(get_embedder())
    create_upload_folder(UPLOADED_FILES_PATH)
    create_index()
    opea_microservices["opea_service@prepare_doc_elastic"].start()
