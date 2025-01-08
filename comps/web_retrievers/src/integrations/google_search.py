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
    OpeaComponent,
    OpeaComponentRegistry,
    SearchedDoc,
    ServiceType,
    TextDoc,
    statistics_dict,
)

logger = CustomLogger("opea_google_search")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_GOOGLE_SEARCH")
class OpeaGoogleSearch(OpeaComponent):
    """A specialized Web Retrieval component derived from OpeaComponent for Google web retriever services."""

    def __init__(self, name: str, description: str, config: dict = None):
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")
        self.google_cse_id = os.environ.get("GOOGLE_CSE_ID")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=50)
        # Create vectorstore
        self.tei_embedding_endpoint = os.getenv("TEI_EMBEDDING_ENDPOINT")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaGoogleSearch health check failed.")

        super().__init__(name, ServiceType.WEB_RETRIEVER.name.lower(), description, config)

    def get_urls(self, query, num_search_result=1):
        result = self.search.results(query, num_search_result)
        return result

    def dump_docs(self, docs):
        batch_size = 32
        for i in range(0, len(docs), batch_size):
            self.vector_db.add_documents(docs[i : i + batch_size])

    def retrieve_htmls(self, all_urls):
        loader = AsyncHtmlLoader(all_urls, ignore_load_errors=True, trust_env=True)
        docs = loader.load()
        return docs

    def parse_htmls(self, docs):
        if logflag:
            logger.info("Indexing new urls...")

        html2text = Html2TextTransformer()
        docs = list(html2text.transform_documents(docs))
        docs = self.text_splitter.split_documents(docs)

        return docs

    async def invoke(self, input: EmbedDoc) -> SearchedDoc:
        """Involve the Google search service to retrieve the documents related to the prompt."""
        # Read the uploaded file
        if logflag:
            logger.info(input)
        start = time.time()
        query = input.text
        embedding = input.embedding

        # Google Search the results, parse the htmls
        search_results = self.get_urls(query=query, num_search_result=input.k)
        urls_to_look = []
        for res in search_results:
            if res.get("link", None):
                urls_to_look.append(res["link"])
        urls = list(set(urls_to_look))
        if logflag:
            logger.info(f"urls: {urls}")
        docs = self.retrieve_htmls(urls)
        docs = self.parse_htmls(docs)
        if logflag:
            logger.info(docs)
        # Remove duplicated docs
        unique_documents_dict = {(doc.page_content, tuple(sorted(doc.metadata.items()))): doc for doc in docs}
        unique_documents = list(unique_documents_dict.values())
        statistics_dict["opea_service@search"].append_latency(time.time() - start, None)

        # dump to vector_db
        self.dump_docs(unique_documents)

        # Do the retrieval
        search_res = await self.vector_db.asimilarity_search_by_vector(embedding=embedding, k=input.k)

        searched_docs = []

        for r in search_res:
            # include the metadata into the retrieved docs content
            description_str = f"\n description: {r.metadata['description']} \n" if "description" in r.metadata else ""
            title_str = f"\n title: {r.metadata['title']} \n" if "title" in r.metadata else ""
            source_str = f"\n source: {r.metadata['source']} \n" if "source" in r.metadata else ""
            text_with_meta = f"{r.page_content} {description_str} {title_str} {source_str}"
            searched_docs.append(TextDoc(text=text_with_meta))

        result = SearchedDoc(retrieved_docs=searched_docs, initial_query=query)
        statistics_dict["opea_service@web_retriever"].append_latency(time.time() - start, None)

        # For Now history is banned
        if self.vector_db.get()["ids"]:
            self.vector_db.delete(self.vector_db.get()["ids"])
        if logflag:
            logger.info(result)
        return result

    def check_health(self) -> bool:
        """Checks the health of the embedding service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        try:
            self.search = GoogleSearchAPIWrapper(
                google_api_key=self.google_api_key, google_cse_id=self.google_cse_id, k=10
            )
            # vectordb_persistent_directory = os.getenv("VECTORDB_PERSISTENT_DIR", "/home/user/chroma_db_oai")
            self.vector_db = Chroma(
                embedding_function=HuggingFaceEndpointEmbeddings(model=self.tei_embedding_endpoint),
                # persist_directory=vectordb_persistent_directory
            )
        except Exception as e:
            logger.error(e)
            return False
        return True
