#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, UnstructuredFileLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Redis
from rag_redis.config import EMBED_MODEL, INDEX_NAME, INDEX_SCHEMA, REDIS_URL

loader = DirectoryLoader(
    "/ws/txt_files", glob="**/*.txt", show_progress=True, use_multithreading=True, loader_cls=TextLoader
)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100, add_start_index=True)

chunks = loader.load_and_split(text_splitter)
print("Done preprocessing. Created", len(chunks), "chunks of the original data")

# Create vectorstore
embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

company_name = "Intel"
_ = Redis.from_texts(
    # appending this little bit can sometimes help with semantic retrieval
    # especially with multiple companies
    texts=[f"Company: {company_name}. " + chunk.page_content for chunk in chunks],
    metadatas=[chunk.metadata for chunk in chunks],
    embedding=embedder,
    index_name=INDEX_NAME,
    index_schema=INDEX_SCHEMA,
    redis_url=REDIS_URL,
)
