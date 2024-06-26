# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import sys

from config import COLLECTION_NAME, EMBED_MODEL, EMBEDDING_ENDPOINT, MILVUS_HOST, MILVUS_PORT
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain_milvus.vectorstores import Milvus
from langchain_text_splitters import HTMLHeaderTextSplitter

from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.proto.docarray import DocPath
from comps.cores.telemetry.opea_telemetry import opea_telemetry
from comps.dataprep.utils import document_loader, get_tables_result

# current_script_path = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_script_path)
# sys.path.append(parent_dir)
# from utils import document_loader


@register_microservice(
    name="opea_service@prepare_doc_milvus",
    endpoint="/v1/dataprep",
    host="0.0.0.0",
    port=6010,
    input_datatype=DocPath,
    output_datatype=None,
)
# @opea_telemetry
def ingest_documents(doc_path: DocPath):
    """Ingest document to Milvus."""
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
    if EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Batch size
    batch_size = 32
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = batch_chunks

        _ = Milvus.from_texts(
            texts=batch_texts,
            embedding=embedder,
            collection_name=COLLECTION_NAME,
            connection_args={"host": MILVUS_HOST, "port": MILVUS_PORT},
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")


if __name__ == "__main__":
    opea_microservices["opea_service@prepare_doc_milvus"].start()
