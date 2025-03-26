# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json

import requests
from tools.redis_kv import RedisKVStore
from tools.utils import *


def get_summary_else_doc(query, company):
    company = company.upper()

    # decide if company is in company list
    company_list = get_company_list()
    print(f"company_list {company_list}")
    company = get_company_name_in_kb(company, company_list)
    if "Cannot find" in company or "Database is empty" in company:
        print(f"Company not found in knowledge base: {company}")
        return company
    print(f"Company {company}")

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
    doc = kvstore.get(doc_title, f"full_doc_{company}")
    doc_length = doc["doc_length"]
    print(f"Doc length: {doc_length}")
    if "summary" not in doc:
        content = doc["full_doc"]
        print(f"is_summary: {False}")
        is_summary = False
        return doc_title, content, is_summary
    content = doc["summary"]
    is_summary = True
    print(f"Summary already exists in KV store: {is_summary}")
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
    doc_dict = kvstore.get(doc_title, f"full_doc_{company}")

    # Add the summary to the dictionary
    doc_dict["summary"] = summary

    # Save the updated value back to the store
    kvstore.put(doc_title, doc_dict, collection=f"full_doc_{company}")


def summarize(doc_name, company):
    ip_address = os.environ.get("ip_address")
    # docsum_url = f"http://{ip_address}:9000/v1/docsum"
    docsum_url = os.environ.get("DOCSUM_ENDPOINT")
    print(f"Docsum Endpoint URL: {docsum_url}")

    doc_title, sum, is_summary = get_summary_else_doc(doc_name, company)
    print(f"Summary or full doc from get_summary_else_doc: {sum[:100]} \n -------\n")
    if is_summary == False:
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
            ret = resp.text
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
    company = "Gap"
    year = "2024"
    quarter = "Q4"

    # company="Costco"
    # year="2025"
    # quarter="Q2"

    print("testing summarize")
    doc_name = f"{company} {year} {quarter} earning call"
    summarize(doc_name, company)
    print("=" * 50)
