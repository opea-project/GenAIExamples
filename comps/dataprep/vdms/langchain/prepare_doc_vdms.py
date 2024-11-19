# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import List, Optional, Union

from config import COLLECTION_NAME, DISTANCE_STRATEGY, EMBED_MODEL, SEARCH_ENGINE, VDMS_HOST, VDMS_PORT
from fastapi import File, Form, HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores.vdms import VDMS, VDMS_Client
from langchain_text_splitters import HTMLHeaderTextSplitter

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    create_upload_folder,
    document_loader,
    encode_filename,
    get_separators,
    get_tables_result,
    parse_html_new,
    save_content_to_local_disk,
)

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
client = VDMS_Client(VDMS_HOST, int(VDMS_PORT))
logger = CustomLogger("prepare_doc_redis")
logflag = os.getenv("LOGFLAG", False)
upload_folder = "./uploaded_files/"


def ingest_data_to_vdms(doc_path: DocPath):
    """Ingest document to VDMS."""
    path = doc_path.path
    print(f"Parsing document {doc_path}.")

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
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        _ = VDMS.from_texts(
            client=client,
            embedding=embedder,
            collection_name=COLLECTION_NAME,
            distance_strategy=DISTANCE_STRATEGY,
            engine=SEARCH_ENGINE,
            texts=batch_texts,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")


@register_microservice(
    name="opea_service@prepare_doc_vdms",
    endpoint="/v1/dataprep",
    host="0.0.0.0",
    port=6007,
)
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

            save_path = upload_folder + encode_file
            await save_content_to_local_disk(save_path, file)
            ingest_data_to_vdms(
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

            save_path = upload_folder + encoded_link + ".txt"
            content = parse_html_new([link], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            await save_content_to_local_disk(save_path, content)
            ingest_data_to_vdms(
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


if __name__ == "__main__":
    create_upload_folder(upload_folder)
    opea_microservices["opea_service@prepare_doc_vdms"].start()
