# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Union

from config import EMBED_MODEL, PINECONE_API_KEY, PINECONE_INDEX_NAME
from fastapi import Body, File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import HTMLHeaderTextSplitter
from pinecone import Pinecone, ServerlessSpec

from comps import CustomLogger, DocPath, opea_microservices, opea_telemetry, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    get_file_structure,
    get_separators,
    get_tables_result,
    parse_html_new,
    remove_folder_with_ignore,
    save_content_to_local_disk,
)

logger = CustomLogger("prepare_doc_pinecone")
logflag = os.getenv("LOGFLAG", False)

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")
upload_folder = "./uploaded_files/"


def check_index_existance():
    if logflag:
        logger.info(f"[ check index existence ] checking {PINECONE_INDEX_NAME}")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing_indexes:
        if logflag:
            logger.info("[ check index existence ] index does not exist")
        return None
    else:
        return True


def create_index(client):
    if logflag:
        logger.info(f"[ create index ] creating index {PINECONE_INDEX_NAME}")
    try:
        client.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        if logflag:
            logger.info(f"[ create index ] index {PINECONE_INDEX_NAME} successfully created")
    except Exception as e:
        if logflag:
            logger.info(f"[ create index ] fail to create index {PINECONE_INDEX_NAME}: {e}")
        return False
    return True


def drop_index(index_name):
    if logflag:
        logger.info(f"[ drop index ] dropping index {index_name}")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    try:
        pc.delete_index(index_name)
        if logflag:
            logger.info(f"[ drop index ] index {index_name} deleted")
    except Exception as e:
        if logflag:
            logger.info(f"[ drop index ] index {index_name} delete failed: {e}")
        return False
    return True


def ingest_data_to_pinecone(doc_path: DocPath):
    """Ingest document to Pinecone."""
    path = doc_path.path
    if logflag:
        logger.info(f"Parsing document {path}.")

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
    if logflag:
        logger.info("Done preprocessing. Created ", len(chunks), " chunks of the original file.")

    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Checking Index existence
    if not check_index_existance():
        # Creating the index
        create_index(pc)
        if logflag:
            logger.info("Successfully created the index", PINECONE_INDEX_NAME)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    file_ids = []

    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        vectorstore = PineconeVectorStore.from_texts(
            texts=batch_texts,
            embedding=embedder,
            index_name=PINECONE_INDEX_NAME,
        )
        if logflag:
            logger.info(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")

    # store file_ids into index file-keys
    pc = Pinecone(api_key=PINECONE_API_KEY)


async def ingest_link_to_pinecone(link_list: List[str], chunk_size, chunk_overlap):
    # Create embedding obj
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Checking Index existence
    if not check_index_existance():
        # Creating the index
        create_index(pc)
        if logflag:
            logger.info("Successfully created the index", PINECONE_INDEX_NAME)

    # save link contents and doc_ids one by one
    for link in link_list:
        content = parse_html_new([link], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if logflag:
            logger.info(f"[ ingest link ] link: {link} content: {content}")
        encoded_link = encode_filename(link)
        save_path = upload_folder + encoded_link + ".txt"
        if logflag:
            logger.info(f"[ ingest link ] save_path: {save_path}")
        await save_content_to_local_disk(save_path, content)

        vectorstore = PineconeVectorStore.from_texts(
            texts=content,
            embedding=embedder,
            index_name=PINECONE_INDEX_NAME,
        )

    return True


@register_microservice(name="opea_service@prepare_doc_pinecone", endpoint="/v1/dataprep", host="0.0.0.0", port=6007)
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1500),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    if logflag:
        logger.info(f"files:{files}")
        logger.info(f"link_list:{link_list}")

    if files:
        if not isinstance(files, list):
            files = [files]
        uploaded_files = []
        for file in files:
            encode_file = encode_filename(file.filename)
            save_path = upload_folder + encode_file
            await save_content_to_local_disk(save_path, file)
            ingest_data_to_pinecone(
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
                logger.info(f"Successfully saved file {save_path}")
        result = {"status": 200, "message": "Data preparation succeeded"}
        if logflag:
            logger.info(result)
        return result

    if link_list:
        try:
            link_list = json.loads(link_list)  # Parse JSON string to list
            if not isinstance(link_list, list):
                raise HTTPException(status_code=400, detail="link_list should be a list.")
            await ingest_link_to_pinecone(link_list, chunk_size, chunk_overlap)
            result = {"status": 200, "message": "Data preparation succeeded"}
            if logflag:
                logger.info(f"Successfully saved link list {link_list}")
                logger.info(result)
            return result
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for link_list.")

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


@register_microservice(
    name="opea_service@prepare_doc_pinecone_file", endpoint="/v1/dataprep/get_file", host="0.0.0.0", port=6008
)
async def rag_get_file_structure():
    if logflag:
        logger.info("[ dataprep - get file ] start to get file structure")

    if not Path(upload_folder).exists():
        if logflag:
            logger.info("No file uploaded, return empty list.")
        return []

    file_content = get_file_structure(upload_folder)
    if logflag:
        logger.info(file_content)
    return file_content


@register_microservice(
    name="opea_service@prepare_doc_pinecone_del", endpoint="/v1/dataprep/delete_file", host="0.0.0.0", port=6009
)
async def delete_all(file_path: str = Body(..., embed=True)):
    """Delete file according to `file_path`.

    `file_path`:
        - "all": delete all files uploaded
    """
    # delete all uploaded files
    if file_path == "all":
        if logflag:
            logger.info("[dataprep - del] delete all files")
        remove_folder_with_ignore(upload_folder)
        assert drop_index(index_name=PINECONE_INDEX_NAME)
        if logflag:
            logger.info("[dataprep - del] successfully delete all files.")
        create_upload_folder(upload_folder)
        if logflag:
            logger.info({"status": True})
        return {"status": True}
    else:
        raise HTTPException(status_code=404, detail="Single file deletion is not implemented yet")


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    opea_microservices["opea_service@prepare_doc_pinecone"].start()
    opea_microservices["opea_service@prepare_doc_pinecone_file"].start()
    opea_microservices["opea_service@prepare_doc_pinecone_del"].start()
