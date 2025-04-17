# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from tools.utils import *


def get_context_bm25_llm(query, company, year, quarter=""):
    k = 5

    company_list = get_company_list()
    company = get_company_name_in_kb(company, company_list)
    if "Cannot find" in company or "Database is empty" in company:
        return company

    print(f"Company: {company}")
    # chunks
    index_name = f"chunks_{company}"
    vector_store = get_vectorstore(index_name)
    chunks_bm25 = bm25_search_broad(query, company, year, quarter, k=k, doc_type="chunks")
    chunks_sim = similarity_search(vector_store, k, query, company, year, quarter)
    chunks = chunks_bm25 + chunks_sim

    # tables
    try:
        index_name = f"tables_{company}"
        vector_store_table = get_vectorstore(index_name)
        # get tables matching metadata
        tables_bm25 = bm25_search_broad(query, company, year, quarter, k=k, doc_type="tables")
        tables_sim = similarity_search(vector_store_table, k, query, company, year, quarter)
        tables = tables_bm25 + tables_sim
    except:
        tables = []

    # get unique results
    context = get_unique_docs(chunks + tables)
    print("Context:\n", context[:500])

    if context:
        query = f"{query} for {company} in {year} {quarter}"
        prompt = ANSWER_PROMPT.format(query=query, documents=context)
        response = generate_answer(prompt)
        response = parse_response(response)
    else:
        response = f"No relevant information found for {company} in {year} {quarter}."
    print("Search result:\n", response)
    return response


def search_full_doc(query, company):
    company = company.upper()

    # decide if company is in company list
    company_list = get_company_list()
    company = get_company_name_in_kb(company, company_list)
    if "Cannot find" in company or "Database is empty" in company:
        return company

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
    content = doc["full_doc"]
    doc_length = doc["doc_length"]
    print(f"Doc length: {doc_length}")
    print(f"Full doc content: {content[:100]}...")
    # once summary is done, can save to kvstore
    # first delete the old record
    # kvstore.delete(doc_title, f"full_doc_{company}")
    # then save the new record with summary
    # kvstore.put(doc_title, {"full_doc": content, "summary":summary,"doc_length":doc_length, **metadata}, f"full_doc_{company}")
    return content


if __name__ == "__main__":
    # company="Gap"
    # year="2024"
    # quarter="Q4"

    company = "Costco"
    year = "2025"
    quarter = "Q2"

    collection_name = f"chunks_{company}"
    search_metadata = ("company", company)

    resp = get_context_bm25_llm("revenue", company, year, quarter)
    print("***Response:\n", resp)
    print("=" * 50)

    print("testing retrieve full doc")
    query = f"{company} {year} {quarter} earning call"
    search_full_doc(query, company)
