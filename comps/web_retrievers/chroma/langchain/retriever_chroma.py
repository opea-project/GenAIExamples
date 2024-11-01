# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from comps import (
    CustomLogger,
    EmbedDoc,
    SearchedDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("web_retriever_chroma")
logflag = os.getenv("LOGFLAG", False)

tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")


def get_urls(query, num_search_result=1):
    result = search.results(query, num_search_result)
    return result


def retrieve_htmls(all_urls):
    loader = AsyncHtmlLoader(all_urls, ignore_load_errors=True, trust_env=True)
    docs = loader.load()
    return docs


def parse_htmls(docs):
    if logflag:
        logger.info("Indexing new urls...")

    html2text = Html2TextTransformer()
    docs = list(html2text.transform_documents(docs))
    docs = text_splitter.split_documents(docs)

    return docs


def dump_docs(docs):
    batch_size = 32
    for i in range(0, len(docs), batch_size):
        vector_db.add_documents(docs[i : i + batch_size])


@register_microservice(
    name="opea_service@web_retriever_chroma",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/web_retrieval",
    host="0.0.0.0",
    port=7077,
)
@register_statistics(names=["opea_service@web_retriever_chroma", "opea_service@search"])
async def web_retrieve(input: EmbedDoc) -> SearchedDoc:
    if logflag:
        logger.info(input)
    start = time.time()
    query = input.text
    embedding = input.embedding

    # Google Search the results, parse the htmls
    search_results = get_urls(query=query, num_search_result=input.k)
    urls_to_look = []
    for res in search_results:
        if res.get("link", None):
            urls_to_look.append(res["link"])
    urls = list(set(urls_to_look))
    if logflag:
        logger.info(f"urls: {urls}")
    docs = retrieve_htmls(urls)
    docs = parse_htmls(docs)
    if logflag:
        logger.info(docs)
    # Remove duplicated docs
    unique_documents_dict = {(doc.page_content, tuple(sorted(doc.metadata.items()))): doc for doc in docs}
    unique_documents = list(unique_documents_dict.values())
    statistics_dict["opea_service@search"].append_latency(time.time() - start, None)

    # dump to vector_db
    dump_docs(unique_documents)

    # Do the retrieval
    search_res = await vector_db.asimilarity_search_by_vector(embedding=embedding, k=input.k)

    searched_docs = []

    for r in search_res:
        # include the metadata into the retrieved docs content
        description_str = f"\n description: {r.metadata['description']} \n" if "description" in r.metadata else ""
        title_str = f"\n title: {r.metadata['title']} \n" if "title" in r.metadata else ""
        source_str = f"\n source: {r.metadata['source']} \n" if "source" in r.metadata else ""
        text_with_meta = f"{r.page_content} {description_str} {title_str} {source_str}"
        searched_docs.append(TextDoc(text=text_with_meta))

    result = SearchedDoc(retrieved_docs=searched_docs, initial_query=query)
    statistics_dict["opea_service@web_retriever_chroma"].append_latency(time.time() - start, None)

    # For Now history is banned
    if vector_db.get()["ids"]:
        vector_db.delete(vector_db.get()["ids"])
    if logflag:
        logger.info(result)
    return result


if __name__ == "__main__":
    # Create vectorstore
    tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")
    # vectordb_persistent_directory = os.getenv("VECTORDB_PERSISTENT_DIR", "/home/user/chroma_db_oai")
    vector_db = Chroma(
        embedding_function=HuggingFaceEndpointEmbeddings(model=tei_embedding_endpoint),
        # persist_directory=vectordb_persistent_directory
    )

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID")
    search = GoogleSearchAPIWrapper(google_api_key=google_api_key, google_cse_id=google_cse_id, k=10)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=50)

    opea_microservices["opea_service@web_retriever_chroma"].start()
