# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
import re
import time
from typing import List, Union

import openai
from config import (
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USERNAME,
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_LLM_MODEL,
    TEI_EMBEDDING_ENDPOINT,
    TGI_LLM_ENDPOINT,
)
from llama_index.core import PropertyGraphIndex, Settings
from llama_index.core.indices.property_graph.sub_retrievers.vector import VectorContextRetriever
from llama_index.core.llms import LLM, ChatMessage
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from llama_index.llms.openai import OpenAI
from llama_index.llms.text_generation_inference import TextGenerationInference
from neo4j import GraphDatabase
from pydantic import BaseModel, PrivateAttr

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
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResponseData,
)
from comps.dataprep.neo4j.llama_index.extract_graph_neo4j import GraphRAGStore, get_attribute_from_tgi_endpoint

logger = CustomLogger("retriever_neo4j")
logflag = os.getenv("LOGFLAG", False)


class GraphRAGQueryEngine(CustomQueryEngine):
    # https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/cookbooks/GraphRAG_v2.ipynb
    # private attr because inherits from BaseModel
    _graph_store: GraphRAGStore = PrivateAttr()
    _index: PropertyGraphIndex = PrivateAttr()
    _llm: LLM = PrivateAttr()
    _similarity_top_k: int = PrivateAttr()

    def __init__(self, graph_store: GraphRAGStore, llm: LLM, index: PropertyGraphIndex, similarity_top_k: int = 20):
        super().__init__()
        self._graph_store = graph_store
        self._index = index
        self._llm = llm
        self._similarity_top_k = similarity_top_k

    def custom_query(self, query_str: str) -> RetrievalResponseData:
        """Process all community summaries to generate answers to a specific query."""

        entities = self.get_entities(query_str, self._similarity_top_k)
        entity_info = self._graph_store.read_entity_info()
        community_ids = self.retrieve_entity_communities(entity_info, entities)
        community_summaries = self.retrieve_community_summaries_cypher(entities)
        community_ids = list(community_summaries.keys())
        if logflag:
            logger.info(f"Community ids: {community_ids}")
        # community_summaries of relevant communities
        community_answers = [
            self.generate_answer_from_summary(community_summary, query_str)
            for id, community_summary in community_summaries.items()
        ]
        # Convert answers to RetrievalResponseData objects
        response_data = [RetrievalResponseData(text=answer, metadata={}) for answer in community_answers]
        return response_data

    def get_entities(self, query_str, similarity_top_k):
        if logflag:
            logger.info(f"Retrieving entities for query: {query_str} with top_k: {similarity_top_k}")
        # TODO: make retrever configurable [VectorContextRetriever]or [LLMSynonymRetriever]
        vecContext_retriever = VectorContextRetriever(
            graph_store=self._graph_store,
            embed_model=self._index._embed_model,
            similarity_top_k=self._similarity_top_k,
            # similarity_score=0.6
        )
        # nodes_retrieved = self._index.as_retriever(
        #    sub_retrievers=[vecContext_retriever], similarity_top_k=self._similarity_top_k
        # ).retrieve(query_str)
        # if subretriever not specified it will use LLMSynonymRetriever with Settings.llm model
        nodes_retrieved = self._index.as_retriever(similarity_top_k=self._similarity_top_k).retrieve(query_str)
        entities = set()
        pattern = r"(\w+(?:\s+\w+)*)\s*->\s*(\w+(?:\s+\w+)*)\s*->\s*(\w+(?:\s+\w+)*)"
        if logflag:
            logger.info(f" len of triplets {len(self._index.property_graph_store.get_triplets())}")
            logger.info(f"number of nodes retrieved {len(nodes_retrieved), nodes_retrieved}")
        for node in nodes_retrieved:
            matches = re.findall(pattern, node.text, re.DOTALL)

            for match in matches:
                subject = match[0]
                obj = match[2]
                entities.add(subject)
                entities.add(obj)
        if logflag:
            logger.info(f"entities from query {entities}")
        return list(entities)

    def retrieve_entity_communities(self, entity_info, entities):
        """Retrieve cluster information for given entities, allowing for multiple clusters per entity.

        Args:
        entity_info (dict): Dictionary mapping entities to their cluster IDs (list).
        entities (list): List of entity names to retrieve information for.

        Returns:
        List of community or cluster IDs to which an entity belongs.
        """
        community_ids = []

        for entity in entities:
            if entity in entity_info:
                community_ids.extend(entity_info[entity])

        return list(set(community_ids))

    def retrieve_community_summaries_cypher(self, entities):
        """Retrieve cluster information and summaries for given entities using a Cypher query.

        Args:
        entities (list): List of entity names to retrieve information for.

        Returns:
        dict: Dictionary where keys are community or cluster IDs and values are summaries.
        """
        community_summaries = {}
        print(f"driver working? {self._graph_store.driver})")

        with self._graph_store.driver.session() as session:
            for entity in entities:
                result = session.run(
                    """
                    MATCH (e:Entity {id: $entity_id})-[:BELONGS_TO]->(c:Cluster)
                    RETURN c.id AS cluster_id, c.summary AS summary
                    """,
                    entity_id=entity,
                )
                for record in result:
                    community_summaries[record["cluster_id"]] = record["summary"]

        return community_summaries

    def generate_answer_from_summary(self, community_summary, query):
        """Generate an answer from a community summary based on a given query using LLM."""
        prompt = (
            f"Given the community summary: {community_summary}, "
            f"how would you answer the following query? Query: {query}"
        )
        messages = [
            ChatMessage(role="system", content=prompt),
            ChatMessage(
                role="user",
                content="I need an answer based on the above information.",
            ),
        ]
        response = self._llm.chat(messages)
        cleaned_response = re.sub(r"^assistant:\s*", "", str(response)).strip()
        return cleaned_response


@register_microservice(
    name="opea_service@retriever_community_answers_neo4j",
    service_type=ServiceType.RETRIEVER,
    endpoint="/v1/retrieval",
    host="0.0.0.0",
    port=6009,
)
@register_statistics(names=["opea_service@retriever_community_answers_neo4j"])
async def retrieve(input: Union[ChatCompletionRequest]) -> Union[ChatCompletionRequest]:
    if logflag:
        logger.info(input)
    start = time.time()

    if isinstance(input.messages, str):
        query = input.messages
    else:
        query = input.messages[0]["content"]
    logger.info(f"Query received in retriever: {query}")

    if OPENAI_API_KEY:
        logger.info("OpenAI API Key is set. Verifying its validity...")
        openai.api_key = OPENAI_API_KEY
        try:
            llm = OpenAI(temperature=0, model=OPENAI_LLM_MODEL)
            embed_model = OpenAIEmbedding(model=OPENAI_EMBEDDING_MODEL, embed_batch_size=100)
            logger.info("OpenAI API Key is valid.")
        except openai.AuthenticationError:
            logger.info("OpenAI API Key is invalid.")
        except Exception as e:
            logger.info(f"An error occurred while verifying the API Key: {e}")
    else:
        logger.info("No OpenAI API KEY provided. Will use TGI and TEI endpoints")
        llm_name = get_attribute_from_tgi_endpoint(TGI_LLM_ENDPOINT, "model_id")
        llm = TextGenerationInference(
            model_url=TGI_LLM_ENDPOINT,
            model_name=llm_name,
            temperature=0.7,
            max_tokens=1512,  # 512otherwise too shor
        )
        emb_name = get_attribute_from_tgi_endpoint(TEI_EMBEDDING_ENDPOINT, "model_id")
        embed_model = TextEmbeddingsInference(
            base_url=TEI_EMBEDDING_ENDPOINT,
            model_name=emb_name,
            timeout=60,  # timeout in seconds
            embed_batch_size=10,  # batch size for embedding
        )
    Settings.embed_model = embed_model
    Settings.llm = llm
    # pre-existiing graph store (created with data_prep/llama-index/extract_graph_neo4j.py)
    graph_store = GraphRAGStore(username=NEO4J_USERNAME, password=NEO4J_PASSWORD, url=NEO4J_URL, llm=llm)

    index = PropertyGraphIndex.from_existing(
        property_graph_store=graph_store,
        embed_model=embed_model or Settings.embed_model,
        embed_kg_nodes=True,
    )

    query_engine = GraphRAGQueryEngine(
        graph_store=index.property_graph_store,
        llm=llm,
        index=index,
        similarity_top_k=3,
    )

    # these are the answers from the community summaries
    answers_by_community = query_engine.query(query)
    input.retrieved_docs = answers_by_community
    input.documents = [doc.text for doc in answers_by_community]
    result = ChatCompletionRequest(
        messages="Retrieval of answers from community summaries successful",
        retrieved_docs=input.retrieved_docs,
        documents=input.documents,
    )

    statistics_dict["opea_service@retriever_community_answers_neo4j"].append_latency(time.time() - start, None)

    if logflag:
        logger.info(result)
    return result


if __name__ == "__main__":
    opea_microservices["opea_service@retriever_community_answers_neo4j"].start()
