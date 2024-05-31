#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

import io
import os

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import ConfluenceLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.vectorstores import Redis

# from PIL import Image
from rag_redis.config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, REDIS_URL

tei_embedding_endpoint = os.getenv("TEI_ENDPOINT")
confluence_access_token = os.getenv("CONFLUENCE_ACCESS_TOKEN")


def wiki_loader(wiki_url, page_ids):
    loader = ConfluenceLoader(
        url=wiki_url,
        token=confluence_access_token,
        confluence_kwargs={"verify_ssl": False},
    )
    print(wiki_url)
    print(page_ids)
    documents = loader.load(page_ids=page_ids, include_attachments=True, limit=50, max_pages=50)
    return documents


def ingest_documents(wiki_url, page_ids):
    """Ingest Wiki Pages to Redis from the variables (wiki_url, page_ids) that
    contains your contents of interest."""

    # Load list of wiki pages
    company_name = "Intel"
    print("Parsing Intel wiki pages", page_ids)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100, add_start_index=True)
    documents = wiki_loader(wiki_url, page_ids)
    content = ""
    for doc in documents:
        content += doc.page_content
    chunks = text_splitter.split_text(content)

    print("Done preprocessing. Created", len(chunks), "chunks of the original pdf")
    # Create vectorstore
    # Create vectorstore
    if tei_embedding_endpoint:
        # create embeddings using TEI endpoint service
        embedder = HuggingFaceHubEmbeddings(model=tei_embedding_endpoint)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)

    # Batch size
    batch_size = 2
    num_chunks = len(chunks)
    for i in range(0, num_chunks, batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = [f"Company: {company_name}. " + chunk for chunk in batch_chunks]

        _ = Redis.from_texts(
            texts=batch_texts,
            embedding=embedder,
            index_name=INDEX_NAME,
            index_schema=INDEX_SCHEMA,
            redis_url=REDIS_URL,
        )
        print(f"Processed batch {i//batch_size + 1}/{(num_chunks-1)//batch_size + 1}")


if __name__ == "__main__":

    wiki_url = "https://wiki.ith.intel.com/"
    page_ids = [3458609323, 3467299836]

    ingest_documents(wiki_url, page_ids)
