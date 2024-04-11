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

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain_pinecone import PineconeVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.callbacks import streaming_stdout

# Make this look better in the docs.
class Question(BaseModel):
    __root__: str

if os.environ.get("PINECONE_API_KEY", None) is None:
    raise Exception("Missing `PINECONE_API_KEY` environment variable.")

if os.environ.get("PINECONE_ENVIRONMENT", None) is None:
    raise Exception("Missing `PINECONE_ENVIRONMENT` environment variable.")

PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX", "langchain-test")
embed_model = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# set_llm_cache for pinecone for semantic search

vectorstore = PineconeVectorStore.from_existing_index(
    PINECONE_INDEX_NAME, embedder
)
retriever = vectorstore.as_retriever(search_type="mmr")

# Define our prompt
template = """
Use the following pieces of context from retrieved
dataset to answer the question. Do not make up an answer if there is no
context provided to help answer it. Include the 'source' and 'start_index'
from the metadata included in the context you used to answer the question

Context:
---------
{context}

---------
Question: {question}
---------

Answer:
"""
prompt = ChatPromptTemplate.from_template(template)

# RAG Chain
model = HuggingFaceEndpoint(
    endpoint_url=TGI_LLM_ENDPOINT,
    max_new_tokens=512,
    top_k=10,
    top_p=0.95,
    typical_p=0.95,
    temperature=0.01,
    repetition_penalty=1.03,
    streaming=True,
    truncate=1024,
)

chain = (
    RunnableParallel({"context": retriever, "question": RunnablePassthrough()}) | prompt | model | StrOutputParser()
).with_types(input_type=Question)
