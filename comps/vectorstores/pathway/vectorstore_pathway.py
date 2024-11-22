# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os

import pathway as pw
from langchain import text_splitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from pathway.xpacks.llm.parsers import ParseUnstructured
from pathway.xpacks.llm.vector_store import VectorStoreServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# This creates a Pathway connector that tracks all the files in the `data/` directory.
# Additions and modifications will be reflected on the index automatically.

data = pw.io.fs.read(
    "./data",
    format="binary",
    mode="streaming",
    with_metadata=True,
)

data_sources = [data]

splitter = text_splitter.TokenTextSplitter(chunk_size=450, chunk_overlap=50)

host = os.getenv("PATHWAY_HOST", "127.0.0.1")
port = int(os.getenv("PATHWAY_PORT", 8666))

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")

if __name__ == "__main__":
    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        logging.info(f"Initializing the embedder from tei_embedding_endpoint: {tei_embedding_endpoint}")
        embeddings = HuggingFaceEndpointEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embeddings = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    server = VectorStoreServer.from_langchain_components(
        *data_sources,
        embedder=embeddings,
        parser=ParseUnstructured(),
        splitter=splitter,
    )

    server.run_server(
        host,
        port=port,
        with_cache=True,
        cache_backend=pw.persistence.Backend.filesystem("./Cache"),
    )
