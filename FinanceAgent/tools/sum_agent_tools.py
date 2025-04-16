# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json

import requests

try:
    from tools.redis_kv import RedisKVStore
    from tools.utils import *
except ImportError:
    from redis_kv import RedisKVStore
    from utils import *


def get_summary_else_doc(query, company):
    # search most similar doc title
    index_name = f"titles_{company}"
    vector_store = get_vectorstore_titles(index_name)
    k = 1
    docs = vector_store.similarity_search(query, k=k)
    if docs:
        doc = docs[0]
        doc_title = doc.page_content
        print(f"Most similar doc title: {doc_title}")

        kvstore = RedisKVStore(redis_uri=REDIS_URL_KV)
        try:
            # Check if summary already exists in the KV store
            content = kvstore.get(f"{doc_title}_summary", f"full_doc_{company}")["summary"]
            is_summary = True
            print("Summary already exists in KV store.")
        except Exception as e:
            doc = kvstore.get(doc_title, f"full_doc_{company}")
            content = doc["full_doc"]
            is_summary = False
            print("No summary found in KV store, returning full document content.")
    else:
        print(f"No similar document found for query: {query}")
        doc_title = None
        content = None
        is_summary = False
    return doc_title, content, is_summary


def save_doc_summary(summary, doc_title, company):
    """Adds a summary to the existing document in the key-value store.

    Args:
        kvstore: The key-value store instance.
        summary: The summary to be added.
        doc_title: The title of the document.
        company: The company associated with the document.
    """
    kvstore = RedisKVStore(redis_uri=REDIS_URL_KV)
    # doc_dict = kvstore.get(doc_title, f"full_doc_{company}")

    # # Add the summary to the dictionary
    # doc_dict["summary"] = summary

    # Save the updated value back to the store
    kvstore.put(f"{doc_title}_summary", {"summary": summary}, collection=f"full_doc_{company}")


def summarize(doc_name, company):
    docsum_url = os.environ.get("DOCSUM_ENDPOINT")
    print(f"Docsum Endpoint URL: {docsum_url}")

    company = format_company_name(company)

    doc_title, sum, is_summary = get_summary_else_doc(doc_name, company)
    if not doc_title:
        return f"Cannot find documents related to {doc_title} in KV store."

    if not is_summary:
        data = {
            "messages": sum,
            "max_tokens": 512,
            "language": "en",
            "stream": False,
            "summary_type": "auto",
            "chunk_size": 2000,
        }

        headers = {"Content-Type": "application/json"}
        try:
            print("Computing Summary with OPEA DocSum...")
            resp = requests.post(url=docsum_url, data=json.dumps(data), headers=headers)
            ret = resp.json()["text"]
            resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
        except requests.exceptions.RequestException as e:
            ret = f"An error occurred:{e}"
        # save summary into db
        print("Saving Summary into KV Store...")
        save_doc_summary(ret, doc_title, company)
        return ret
    else:
        return sum


if __name__ == "__main__":
    # company = "Gap"
    # year = "2024"
    # quarter = "Q4"

    company = "Costco"
    year = "2025"
    quarter = "Q2"

    print("testing summarize")
    doc_name = f"{company} {year} {quarter} earning call"
    ret = summarize(doc_name, company)
    print("Summary: ", ret)
    print("=" * 50)
