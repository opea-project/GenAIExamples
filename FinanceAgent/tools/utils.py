# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from openai import OpenAI

try:
    from tools.redis_kv import RedisKVStore
except ImportError:
    from redis_kv import RedisKVStore

# Embedding model
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
TEI_EMBEDDING_ENDPOINT = os.getenv("TEI_EMBEDDING_ENDPOINT", "")

# Redis URL
REDIS_URL_VECTOR = os.getenv("REDIS_URL_VECTOR", "redis://localhost:6379/")
REDIS_URL_KV = os.getenv("REDIS_URL_KV", "redis://localhost:6380/")

# LLM config
LLM_MODEL = os.getenv("model", "meta-llama/Llama-3.3-70B-Instruct")
LLM_ENDPOINT = os.getenv("llm_endpoint_url", "http://localhost:8086")
print(f"LLM endpoint: {LLM_ENDPOINT}")
MAX_TOKENS = 1024
TEMPERATURE = 0.2

COMPANY_NAME_PROMPT = """\
Here is the list of company names in the knowledge base:
{company_list}

This is the company of interest: {company}

Determine if the company of interest is the same as any of the companies in the knowledge base.
If yes, map the company of interest to the company name in the knowledge base. Output the company name in  {{}}. Example: {{3M}}.
If none of the companies in the knowledge base match the company of interest, output "NONE".
"""

ANSWER_PROMPT = """\
You are a financial analyst. Read the documents below and answer the question.
Documents:
{documents}

Question: {query}
Now take a deep breath and think step by step to answer the question. Wrap your final answer in {{}}. Example: {{The company has a revenue of $100 million.}}
"""


def format_company_name(company):
    company = company.upper()

    # decide if company is in company list
    company_list = get_company_list()
    print(f"company_list {company_list}")
    company = get_company_name_in_kb(company, company_list)
    if "Cannot find" in company or "Database is empty" in company:
        raise ValueError(f"Company not found in knowledge base: {company}")
    print(f"Company: {company}")
    return company


def get_embedder():
    if TEI_EMBEDDING_ENDPOINT:
        # create embeddings using TEI endpoint service
        # Huggingface API token for TEI embedding endpoint
        HF_TOKEN = os.getenv("HF_TOKEN", "")
        assert HF_TOKEN, "HuggingFace API token is required for TEI embedding endpoint."
        embedder = HuggingFaceEndpointEmbeddings(model=TEI_EMBEDDING_ENDPOINT)
    else:
        # create embeddings using local embedding model
        embedder = HuggingFaceBgeEmbeddings(model_name=EMBED_MODEL)
    return embedder


def generate_answer(prompt):
    """Use vllm endpoint to generate the answer."""
    # send request to vllm endpoint
    client = OpenAI(
        base_url=f"{LLM_ENDPOINT}/v1",
        api_key="token-abc123",
    )

    params = {
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    completion = client.chat.completions.create(
        model=LLM_MODEL, messages=[{"role": "user", "content": prompt}], **params
    )

    # get response
    response = completion.choices[0].message.content
    print(f"LLM Response: {response}")
    return response


def parse_response(response):
    if "{" in response:
        ret = response.split("{")[1].split("}")[0]
    else:
        ret = ""
    return ret


def get_company_list():
    kvstore = RedisKVStore(redis_uri=REDIS_URL_KV)
    company_list_dict = kvstore.get("company", "company_list")
    if company_list_dict:
        company_list = company_list_dict["company"]
        return company_list
    else:
        return []


def get_company_name_in_kb(company, company_list):
    if not company_list:
        return "Database is empty."

    company = company.upper()
    if company in company_list:
        return company

    prompt = COMPANY_NAME_PROMPT.format(company_list=company_list, company=company)
    response = generate_answer(prompt)
    if "NONE" in response.upper():
        return f"Cannot find {company} in knowledge base."
    else:
        ret = parse_response(response)
        if ret:
            return ret
        else:
            return "Failed to parse LLM response."


def get_docs_matching_metadata(metadata, collection_name):
    """
    metadata: ("company_year", "3M_2023")
    docs: list of documents
    """
    key = metadata[0]
    value = metadata[1]
    kvstore = RedisKVStore(redis_uri=REDIS_URL_KV)
    collection = kvstore.get_all(collection_name)  # collection is a dict

    matching_docs = []
    for idx in collection:
        doc = collection[idx]
        if doc["metadata"][key] == value:
            print(f"Found doc with matching metadata {metadata}")
            print(doc["metadata"]["doc_title"])
            matching_docs.append(doc)
    print(f"Number of docs found with search_metadata {metadata}: {len(matching_docs)}")
    return matching_docs


def convert_docs(docs):
    # docs: list of dicts
    converted_docs_content = []
    converted_docs_summary = []
    for doc in docs:
        content = doc["content"]
        # convert content to Document object
        metadata = {"type": "content", **doc["metadata"]}
        converted_content = Document(id=doc["metadata"]["doc_id"], page_content=content, metadata=metadata)

        # convert summary to Document object
        metadata = {"type": "summary", "content": content, **doc["metadata"]}
        converted_summary = Document(id=doc["metadata"]["doc_id"], page_content=doc["summary"], metadata=metadata)
        converted_docs_content.append(converted_content)
        converted_docs_summary.append(converted_summary)
    return converted_docs_content, converted_docs_summary


def bm25_search(query, metadata, company, doc_type="chunks", k=10):
    collection_name = f"{doc_type}_{company}"
    print(f"Collection name: {collection_name}")

    docs = get_docs_matching_metadata(metadata, collection_name)

    if docs:
        docs_text, docs_summary = convert_docs(docs)
        # BM25 search over content
        retriever = BM25Retriever.from_documents(docs_text, k=k)
        docs_bm25 = retriever.invoke(query)
        print(f"BM25: Found {len(docs_bm25)} docs over content with search metadata: {metadata}")

        # BM25 search over summary/title
        retriever = BM25Retriever.from_documents(docs_summary, k=k)
        docs_bm25_summary = retriever.invoke(query)
        print(f"BM25: Found {len(docs_bm25_summary)} docs over summary with search metadata: {metadata}")
        results = docs_bm25 + docs_bm25_summary
    else:
        results = []
    return results


def bm25_search_broad(query, company, year, quarter, k=10, doc_type="chunks"):
    # search with company filter, but query is query_company_quarter
    metadata = ("company", f"{company}")
    query1 = f"{query} {year} {quarter}"
    docs1 = bm25_search(query1, metadata, company, k=k, doc_type=doc_type)

    # search with metadata filters
    metadata = ("company_year_quarter", f"{company}_{year}_{quarter}")
    print(f"BM25: Searching for docs with metadata: {metadata}")
    docs = bm25_search(query, metadata, company, k=k, doc_type=doc_type)
    if not docs:
        print("BM25: No docs found with company, year and quarter filter, only search with company and year filter")
        metadata = ("company_year", f"{company}_{year}")
        docs = bm25_search(query, metadata, company, k=k, doc_type=doc_type)
    if not docs:
        print("BM25: No docs found with company and year filter, only search with company filter")
        metadata = ("company", f"{company}")
        docs = bm25_search(query, metadata, company, k=k, doc_type=doc_type)

    docs = docs + docs1
    if docs:
        return docs
    else:
        return []


def set_filter(metadata_filter):
    # metadata_filter: tuple of (key, value)
    from redisvl.query.filter import Text

    key = metadata_filter[0]
    value = metadata_filter[1]
    filter_condition = Text(key) == value
    return filter_condition


def similarity_search(vector_store, k, query, company, year, quarter=None):
    query1 = f"{query} {year} {quarter}"
    filter_condition = set_filter(("company", company))
    docs1 = vector_store.similarity_search(query1, k=k, filter=filter_condition)
    print(f"Similarity search: Found {len(docs1)} docs with company filter and query: {query1}")

    filter_condition = set_filter(("company_year_quarter", f"{company}_{year}_{quarter}"))
    docs = vector_store.similarity_search(query, k=k, filter=filter_condition)

    if not docs:  # if no relevant document found, relax the filter
        print("No relevant document found with company, year and quarter filter, only search with company and year")
        filter_condition = set_filter(("company_year", f"{company}_{year}"))
        docs = vector_store.similarity_search(query, k=k, filter=filter_condition)

    if not docs:  # if no relevant document found, relax the filter
        print("No relevant document found with company_year filter, only search with company.....")
        filter_condition = set_filter(("company", company))
        docs = vector_store.similarity_search(query, k=k, filter=filter_condition)

    print(f"Similarity search: Found {len(docs)} docs with filter and query: {query}")

    docs = docs + docs1
    if not docs:
        return []
    else:
        return docs


def get_index_name(doc_type: str, metadata: dict):
    company = metadata["company"]
    if doc_type == "chunks":
        index_name = f"chunks_{company}"
    elif doc_type == "tables":
        index_name = f"tables_{company}"
    elif doc_type == "titles":
        index_name = f"titles_{company}"
    elif doc_type == "full_doc":
        index_name = f"full_doc_{company}"
    else:
        raise ValueError("doc_type should be either chunks, tables, titles, or full_doc.")
    return index_name


def get_content(doc):
    # doc can be converted doc
    # of saved doc in vector store
    if "type" in doc.metadata and doc.metadata["type"] == "summary":
        print("BM25 retrieved doc...")
        content = doc.metadata["content"]
    elif "type" in doc.metadata and doc.metadata["type"] == "content":
        print("BM25 retrieved doc...")
        content = doc.page_content
    else:
        print("Dense retriever doc...")

        doc_id = doc.metadata["doc_id"]
        # doc_summary=doc.page_content
        kvstore = RedisKVStore(redis_uri=REDIS_URL_KV)
        collection_name = get_index_name(doc.metadata["doc_type"], doc.metadata)
        result = kvstore.get(doc_id, collection_name)
        content = result["content"]

    # print(f"***Doc Metadata:\n{doc.metadata}")
    # print(f"***Content: {content[:100]}...")

    return content


def get_unique_docs(docs):
    results = []
    context = ""
    i = 1
    for doc in docs:
        content = get_content(doc)
        if content not in results:
            results.append(content)
            doc_title = doc.metadata["doc_title"]
            ret_doc = f"Doc [{i}] from {doc_title}:\n{content}\n"
            context += ret_doc
            i += 1
    print(f"Number of unique docs found: {len(results)}")
    return context


def get_vectorstore(index_name):
    config = RedisConfig(
        index_name=index_name,
        redis_url=REDIS_URL_VECTOR,
        metadata_schema=[
            {"name": "company", "type": "text"},
            {"name": "year", "type": "text"},
            {"name": "quarter", "type": "text"},
            {"name": "doc_type", "type": "text"},
            {"name": "doc_title", "type": "text"},
            {"name": "doc_id", "type": "text"},
            {"name": "company_year", "type": "text"},
            {"name": "company_year_quarter", "type": "text"},
        ],
    )
    embedder = get_embedder()
    vector_store = RedisVectorStore(embedder, config=config)
    return vector_store


def get_vectorstore_titles(index_name):
    config = RedisConfig(
        index_name=index_name,
        redis_url=REDIS_URL_VECTOR,
        metadata_schema=[
            {"name": "company", "type": "text"},
            {"name": "year", "type": "text"},
            {"name": "quarter", "type": "text"},
            {"name": "doc_type", "type": "text"},
            {"name": "doc_title", "type": "text"},
            {"name": "company_year", "type": "text"},
            {"name": "company_year_quarter", "type": "text"},
        ],
    )
    embedder = get_embedder()
    vector_store = RedisVectorStore(embedder, config=config)
    return vector_store
