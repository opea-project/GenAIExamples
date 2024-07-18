# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from config import EMBED_MODEL, PINECONE_API_KEY, PINECONE_INDEX_NAME
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Pinecone

from comps import DocPath, opea_microservices, opea_telemetry, register_microservice
from comps.dataprep.utils import document_loader, get_separators

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")


@register_microservice(
    name="opea_service@prepare_doc_pinecone",
    endpoint="/v1/dataprep",
    host="0.0.0.0",
    port=6000,
    input_datatype=DocPath,
    output_datatype=None,
)
@opea_telemetry
def ingest_documents(doc_path: DocPath):
    """Ingest document to Pinecone."""
    doc_path = doc_path.path
    print(f"Parsing document {doc_path}.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, chunk_overlap=100, add_start_index=True, separators=get_separators()
    )
    content = document_loader(doc_path)
    chunks = text_splitter.split_text(content)

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

        _ = Pinecone.from_texts(
            texts=batch_texts,
            embedding=embedder,
            index_name=PINECONE_INDEX_NAME,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")


if __name__ == "__main__":
    opea_microservices["opea_service@prepare_doc_pinecone"].start()
