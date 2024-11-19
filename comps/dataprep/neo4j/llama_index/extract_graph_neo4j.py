# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# GraphRAGExtractor dependencies
import asyncio
import json
import os

# GraphRAGStore dependencies
import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

import nest_asyncio
import networkx as nx
import openai
import requests
from config import (
    NEO4J_PASSWORD,
    NEO4J_URL,
    NEO4J_USERNAME,
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_LLM_MODEL,
    TEI_EMBEDDING_ENDPOINT,
    TGI_LLM_ENDPOINT,
    host_ip,
)
from fastapi import File, Form, HTTPException, UploadFile
from graspologic.partition import hierarchical_leiden
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import HTMLHeaderTextSplitter
from llama_index.core import Document, PropertyGraphIndex, Settings
from llama_index.core.llms import ChatMessage
from llama_index.core.node_parser import LangchainNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.openai import OpenAI
from llama_index.llms.text_generation_inference import TextGenerationInference
from neo4j import GraphDatabase
from openai import Client
from transformers import AutoTokenizer

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    document_loader,
    encode_filename,
    get_separators,
    get_tables_result,
    parse_html_new,
    save_content_to_local_disk,
)

nest_asyncio.apply()

from llama_index.core.async_utils import run_jobs
from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.core.graph_stores.types import KG_NODES_KEY, KG_RELATIONS_KEY, EntityNode, Relation
from llama_index.core.indices.property_graph.utils import default_parse_triplets_fn
from llama_index.core.llms.llm import LLM
from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.default_prompts import DEFAULT_KG_TRIPLET_EXTRACT_PROMPT
from llama_index.core.schema import BaseNode, TransformComponent


class GraphRAGStore(Neo4jPropertyGraphStore):
    # https://github.com/run-llama/llama_index/blob/main/docs/docs/examples/cookbooks/GraphRAG_v2.ipynb
    community_summary = {}
    entity_info = None
    max_cluster_size = 100

    def __init__(self, username: str, password: str, url: str, llm: LLM):
        super().__init__(username=username, password=password, url=url)
        self.llm = llm
        self.driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def generate_community_summary(self, text):
        """Generate summary for a given text using an LLM."""
        # Get model information from the TGI endpoint
        model_name = get_attribute_from_tgi_endpoint(TGI_LLM_ENDPOINT, "model_id")
        max_input_length = get_attribute_from_tgi_endpoint(TGI_LLM_ENDPOINT, "max_input_length")
        if not model_name or not max_input_length:
            raise ValueError(f"Could not retrieve model information from TGI endpoint: {TGI_LLM_ENDPOINT}")

        # Get the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are provided with a set of relationships from a knowledge graph, each represented as "
                    "entity1->entity2->relation->relationship_description. Your task is to create a summary of these "
                    "relationships. The summary should include the names of the entities involved and a concise synthesis "
                    "of the relationship descriptions. The goal is to capture the most critical and relevant details that "
                    "highlight the nature and significance of each relationship. Ensure that the summary is coherent and "
                    "integrates the information in a way that emphasizes the key aspects of the relationships."
                ),
            ),
            ChatMessage(role="user", content=text),
        ]
        # Trim the messages to fit within the token limit
        # Microsoft does more sophisticated content optimization
        trimmed_messages = trim_messages_to_token_limit(tokenizer, messages, max_input_length)

        if OPENAI_API_KEY:
            response = OpenAI().chat(messages)
        else:
            response = self.llm.chat(trimmed_messages)

        clean_response = re.sub(r"^assistant:\s*", "", str(response)).strip()
        return clean_response

    def build_communities(self):
        """Builds communities from the graph and summarizes them."""
        nx_graph = self._create_nx_graph()
        community_hierarchical_clusters = hierarchical_leiden(nx_graph, max_cluster_size=self.max_cluster_size)
        logger.info(f"Number of clustered entities: {len(community_hierarchical_clusters)}")
        logger.info(f"Community hierarchical clusters: {community_hierarchical_clusters}")
        n_clusters = set([hc.cluster for hc in community_hierarchical_clusters])
        logger.info(f"number of communities/clusters: {len(n_clusters)}")
        self.entity_info, community_info = self._collect_community_info(nx_graph, community_hierarchical_clusters)
        # self._print_cluster_info(self.entity_info, community_info)
        self.save_entity_info(self.entity_info)
        # entity_from_db = self.read_entity_info()  # to verify if the data is stored in db
        self._summarize_communities(community_info)
        # sum = self.read_all_community_summaries()  # to verify summaries are stored in db

    def _create_nx_graph(self):
        """Converts internal graph representation to NetworkX graph."""
        nx_graph = nx.Graph()
        triplets = self.get_triplets()  # [src, rel, tgt]
        for entity1, relation, entity2 in triplets:
            nx_graph.add_node(entity1.name)
            nx_graph.add_node(entity2.name)
            nx_graph.add_edge(
                relation.source_id,
                relation.target_id,
                relationship=relation.label,
                description=relation.properties["relationship_description"],
            )
        return nx_graph

    def _collect_community_info(self, nx_graph, clusters):
        """Collect information for each node based on their community,
        allowing entities to belong to multiple clusters."""
        entity_info = defaultdict(set)
        community_info = defaultdict(list)

        for item in clusters:
            node = item.node
            cluster_id = item.cluster

            # Update entity_info
            entity_info[node].add(cluster_id)

            for neighbor in nx_graph.neighbors(node):
                edge_data = nx_graph.get_edge_data(node, neighbor)
                if edge_data:
                    detail = f"{node} -> {neighbor} -> {edge_data['relationship']} -> {edge_data['description']}"
                    community_info[cluster_id].append(detail)

        # Convert sets to lists for easier serialization if needed
        entity_info = {k: list(v) for k, v in entity_info.items()}

        return dict(entity_info), dict(community_info)

    def _print_cluster_info(self, entity_info, community_info):
        """Print detailed information about each community cluster.

        Args:
            entity_info (dict): Dictionary where keys are nodes and values are lists of cluster IDs the node belongs to.
            community_info (dict): Dictionary where keys are cluster IDs and values are lists of relationship details within the cluster.
        """
        print("Community Cluster Information:\n")

        for cluster_id, details in community_info.items():
            print(f"Cluster ID: {cluster_id}")
            print("Nodes in this cluster:")

            # Find nodes that belong to this cluster
            nodes_in_cluster = [node for node, clusters in entity_info.items() if cluster_id in clusters]
            for node in nodes_in_cluster:
                print(f"  - Node: {node}")

            print("Relationships in this cluster:")
            for detail in details:
                print(f"  - {detail}")

            print("\n" + "-" * 40 + "\n")

    def save_entity_info(self, entity_info: dict) -> None:
        with self.driver.session() as session:
            for entity_id, cluster_ids in entity_info.items():
                entity_node = EntityNode(id=entity_id, name=str(entity_id))
                for cluster_id in cluster_ids:
                    cluster_node = EntityNode(id=int(cluster_id), name=str(cluster_id))
                    relation_metadata = {"relationship_description": "BELONGS_TO"}
                    rel_node = Relation(
                        label="BELONGS_TO",
                        source_id=entity_node.id,
                        target_id=cluster_node.id,
                        properties=relation_metadata,
                    )

                    session.run(
                        """
                        MERGE (e:Entity {id: $entity_id, name: $entity_name})
                        MERGE (c:Cluster {id: $cluster_id, name: $cluster_name})
                        MERGE (e)-[r:BELONGS_TO]->(c)
                        ON CREATE SET r.relationship_description = $relationship_description
                        """,
                        entity_id=entity_node.id,
                        entity_name=entity_node.name,
                        cluster_id=cluster_node.id,
                        cluster_name=cluster_node.name,
                        relationship_description=relation_metadata["relationship_description"],
                    )

    def read_entity_info(self) -> dict:
        entity_info = {}
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity)-[:BELONGS_TO]->(c:Cluster)
                RETURN e.id AS entity_id, collect(DISTINCT c.id) AS cluster_ids
                """
            )
            for record in result:
                # entity_info[record['entity_id']] = record['cluster_ids']
                entity_info[record["entity_id"]] = [int(cluster_id) for cluster_id in record["cluster_ids"]]
        return entity_info

    def _summarize_communities(self, community_info):
        """Generate and store summaries for each community."""
        for community_id, details in community_info.items():
            logger.info(f"Summarizing community {community_id}")
            details_text = "\n".join(details) + "."  # Ensure it ends with a period
            self.community_summary[community_id] = self.generate_community_summary(details_text)

            # To store summaries in neo4j
            summary = self.generate_community_summary(details_text)
            self.store_community_summary_in_neo4j(community_id, summary)
            # self.community_summary[
            #     community_id
            # ] = self.store_community_summary_in_neo4j(community_id, summary)

    def store_community_summary_in_neo4j(self, community_id, summary):
        """Store the community summary in Neo4j."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Cluster {id: $community_id})
                SET c.summary = $summary
            """,
                community_id=int(community_id),
                summary=summary,
            )

    def read_all_community_summaries(self) -> dict:
        """Read all community summaries from Neo4j."""
        community_summaries = {}
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Cluster)
                RETURN c.id AS community_id, c.summary AS summary
                """
            )
            for record in result:
                community_summaries[int(record["community_id"])] = record["summary"]
        return community_summaries

    def query_schema(self):
        """Query and print the schema information from Neo4j."""
        with self.driver.session() as session:
            result = session.run("CALL apoc.meta.schema()")
            schema = result.single()["value"]

            for label, properties in schema.items():
                if "properties" in properties:
                    print(f"Node Label: {label}")
                    for prop, prop_info in properties["properties"].items():
                        print(f"  Property Key: {prop}, Type: {prop_info['type']}")
                if "relationships" in properties:
                    for rel_type, rel_info in properties["relationships"].items():
                        print(f"Relationship Type: {rel_type}")
                        for prop, prop_info in rel_info["properties"].items():
                            print(f"  Property Key: {prop}, Type: {prop_info['type']}")


class GraphRAGExtractor(TransformComponent):
    """Extract triples from a graph.

    Uses an LLM and a simple prompt + output parsing to extract paths (i.e. triples) and entity, relation descriptions from text.

    Args:
        llm (LLM):
            The language model to use.
        extract_prompt (Union[str, PromptTemplate]):
            The prompt to use for extracting triples.
        parse_fn (callable):
            A function to parse the output of the language model.
        num_workers (int):
            The number of workers to use for parallel processing.
        max_paths_per_chunk (int):
            The maximum number of paths to extract per chunk.
    """

    llm: LLM
    extract_prompt: PromptTemplate
    parse_fn: Callable
    num_workers: int
    max_paths_per_chunk: int

    def __init__(
        self,
        llm: Optional[LLM] = None,
        extract_prompt: Optional[Union[str, PromptTemplate]] = None,
        parse_fn: Callable = default_parse_triplets_fn,
        max_paths_per_chunk: int = 4,
        num_workers: int = 10,
    ) -> None:
        """Init params."""
        from llama_index.core import Settings

        if isinstance(extract_prompt, str):
            extract_prompt = PromptTemplate(extract_prompt)

        super().__init__(
            llm=llm,
            extract_prompt=extract_prompt or DEFAULT_KG_TRIPLET_EXTRACT_PROMPT,
            parse_fn=parse_fn,
            num_workers=num_workers,
            max_paths_per_chunk=max_paths_per_chunk,
        )

    @classmethod
    def class_name(cls) -> str:
        return "GraphExtractor"

    def __call__(self, nodes: List[BaseNode], show_progress: bool = False, **kwargs: Any) -> List[BaseNode]:
        """Extract triples from nodes."""
        return asyncio.run(self.acall(nodes, show_progress=show_progress, **kwargs))

    async def _aextract(self, node: BaseNode) -> BaseNode:
        """Extract triples from a node."""
        assert hasattr(node, "text")

        text = node.get_content(metadata_mode="llm")
        try:
            llm_response = await self.llm.apredict(
                self.extract_prompt,
                text=text,
                max_knowledge_triplets=self.max_paths_per_chunk,
            )
            entities, entities_relationship = self.parse_fn(llm_response)
        except ValueError:
            entities = []
            entities_relationship = []

        existing_nodes = node.metadata.pop(KG_NODES_KEY, [])
        existing_relations = node.metadata.pop(KG_RELATIONS_KEY, [])
        entity_metadata = node.metadata.copy()
        for entity, entity_type, description in entities:
            entity_metadata["entity_description"] = description
            entity_node = EntityNode(name=entity, label=entity_type, properties=entity_metadata)
            existing_nodes.append(entity_node)

        relation_metadata = node.metadata.copy()
        for triple in entities_relationship:
            subj, obj, rel, description = triple
            relation_metadata["relationship_description"] = description
            rel_node = Relation(
                label=rel,
                source_id=subj,
                target_id=obj,
                properties=relation_metadata,
            )

            existing_relations.append(rel_node)

        node.metadata[KG_NODES_KEY] = existing_nodes
        node.metadata[KG_RELATIONS_KEY] = existing_relations
        logger.info(f"number of extracted nodes {len(existing_nodes), existing_nodes}")
        logger.info(f"number of extracted relations {len(existing_relations), existing_relations}")
        return node

    async def acall(self, nodes: List[BaseNode], show_progress: bool = False, **kwargs: Any) -> List[BaseNode]:
        """Extract triples from nodes async."""
        jobs = []
        for node in nodes:
            jobs.append(self._aextract(node))

        return await run_jobs(
            jobs,
            workers=self.num_workers,
            show_progress=show_progress,
            desc="Extracting paths from text",
        )


KG_TRIPLET_EXTRACT_TMPL = """
-Goal-
Given a text document, identify all entities and their entity types from the text and all relationships among the identified entities.
Given the text, extract up to {max_knowledge_triplets} entity-relation triplets.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: Type of the entity
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity strictly as ("entity"$$$$<entity_name>$$$$<entity_type>$$$$<entity_description>). Pay attention to the dollar signs ($$$$) separating the fields and the parentheses surrounding the entire entity.
one example: ("entity"$$$$Apple$$$$Company$$$$Apple Inc. is an American multinational technology company that specializes in consumer electronics, computer software, and online services.)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relation: relationship between source_entity and target_entity
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other

Format each relationship strictly as ("relationship"$$$$<source_entity>$$$$<target_entity>$$$$<relation>$$$$<relationship_description>). Pay attention to the dollar signs ($$$$) separating the fields and the parentheses surrounding the entire entity.
one example: ("relationship"$$$$Apple$$$$Steve Jobs$$$$Founded$$$$Steve Jobs co-founded Apple Inc. in 1976.)

3. When finished, output.

-Real Data-
######################
text: {text}
######################
output:"""

entity_pattern = r'\("entity"\$\$\$\$(.+?)\$\$\$\$(.+?)\$\$\$\$(.+?)\)'
relationship_pattern = r'\("relationship"\$\$\$\$(.+?)\$\$\$\$(.+?)\$\$\$\$(.+?)\$\$\$\$(.+?)\)'


def parse_fn(response_str: str) -> Any:
    entities = re.findall(entity_pattern, response_str)
    relationships = re.findall(relationship_pattern, response_str)
    if logflag:
        logger.info(f"len of parsed entities: {len(entities)} and relationships: {len(relationships)}")
    return entities, relationships


def get_attribute_from_tgi_endpoint(url, attribute_name):
    """Get a specific attribute from the TGI endpoint."""
    try:
        response = requests.get(f"{url}/info")
        response.raise_for_status()  # Ensure we notice bad responses
        try:
            model_info = response.json()
            attribute_value = model_info.get(attribute_name)
            if attribute_value is not None:
                return attribute_value
            else:
                logger.error(f"{attribute_name} not found in the response from {url}")
                return None
        except ValueError:
            logger.error(f"Invalid JSON response from {url}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request to {url} failed: {e}")
        return None


def trim_messages_to_token_limit(tokenizer, messages, max_tokens):
    """Trim the messages to fit within the token limit."""
    total_tokens = 0
    trimmed_messages = []

    for message in messages:
        tokens = tokenizer.tokenize(message.content)
        total_tokens += len(tokens)
        if total_tokens > max_tokens:
            # Trim the message to fit within the remaining token limit
            logger.info(f"Trimming messages: {total_tokens} > {max_tokens}")
            remaining_tokens = max_tokens - (total_tokens - len(tokens))
            tokens = tokens[:remaining_tokens]
            message.content = tokenizer.convert_tokens_to_string(tokens)
            trimmed_messages.append(message)
            break
        else:
            trimmed_messages.append(message)

    return trimmed_messages


logger = CustomLogger("prepare_doc_neo4j")
logflag = os.getenv("LOGFLAG", False)

upload_folder = "./uploaded_files/"
client = OpenAI()


def ingest_data_to_neo4j(doc_path: DocPath):
    """Ingest document to Neo4J."""
    path = doc_path.path
    if logflag:
        logger.info(f"Parsing document {path}.")

    if path.endswith(".html"):
        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        text_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    else:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=doc_path.chunk_size,
            chunk_overlap=doc_path.chunk_overlap,
            add_start_index=True,
            separators=get_separators(),
        )

    content = document_loader(path)  # single doc string
    document = Document(text=content)

    structured_types = [".xlsx", ".csv", ".json", "jsonl"]
    _, ext = os.path.splitext(path)

    # create llama-index nodes (chunks)
    if ext in structured_types:
        nodes = [document]
    else:
        parser = LangchainNodeParser(text_splitter)  # wrap text splitting from langchain w node parser
        nodes = parser.get_nodes_from_documents([document])

    if doc_path.process_table and path.endswith(".pdf"):
        table_chunks = get_tables_result(path, doc_path.table_strategy)  # list of text
        if table_chunks:
            table_docs = [Document(text=chunk) for chunk in table_chunks]
            nodes = nodes + table_docs
            if logflag:
                logger.info(f"extract tables nodes: len of table_docs  {len(table_docs)}")

    if logflag:
        logger.info(f"Done preprocessing. Created  {len(nodes)} chunks of the original file.")

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
        logger.info("NO OpenAI API Key. TGI/TEI endpoints will be used.")
        llm_name = get_attribute_from_tgi_endpoint(TGI_LLM_ENDPOINT, "model_id")
        llm = TextGenerationInference(
            model_url=TGI_LLM_ENDPOINT,
            model_name=llm_name,
            temperature=0.7,
            max_tokens=1512,
            timeout=600,  # timeout in seconds
        )
        emb_name = get_attribute_from_tgi_endpoint(TEI_EMBEDDING_ENDPOINT, "model_id")
        embed_model = TextEmbeddingsInference(
            base_url=TEI_EMBEDDING_ENDPOINT,
            model_name=emb_name,
            timeout=600,  # timeout in seconds
            embed_batch_size=10,  # batch size for embedding
        )
    Settings.embed_model = embed_model
    Settings.llm = llm
    kg_extractor = GraphRAGExtractor(
        llm=llm,
        extract_prompt=KG_TRIPLET_EXTRACT_TMPL,
        max_paths_per_chunk=2,
        parse_fn=parse_fn,
    )
    graph_store = GraphRAGStore(username=NEO4J_USERNAME, password=NEO4J_PASSWORD, url=NEO4J_URL, llm=llm)

    # nodes are the chunked docs to insert
    index = PropertyGraphIndex(
        nodes=nodes,
        llm=llm,
        kg_extractors=[kg_extractor],
        property_graph_store=graph_store,
        embed_model=embed_model or Settings.embed_model,
        show_progress=True,
    )
    if logflag:
        logger.info("The graph is built.")
        logger.info(f"Total number of triplets {len(index.property_graph_store.get_triplets())}")

    if logflag:
        logger.info("Done building communities.")

    return index


def build_communities(index: PropertyGraphIndex):
    try:
        index.property_graph_store.build_communities()
        if logflag:
            logger.info("Done building communities.")
    except Exception as e:
        logger.error(f"Error building communities: {e}")
    return True


@register_microservice(
    name="opea_service@extract_graph_neo4j",
    endpoint="/v1/dataprep",
    host="0.0.0.0",
    port=6004,
    input_datatype=DocPath,
    output_datatype=None,
)
async def ingest_documents(
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    link_list: Optional[str] = Form(None),
    chunk_size: int = Form(1500),
    chunk_overlap: int = Form(100),
    process_table: bool = Form(False),
    table_strategy: str = Form("fast"),
):
    if logflag:
        logger.info(f"files:{files}")
        logger.info(f"link_list:{link_list}")

    if files:
        if not isinstance(files, list):
            files = [files]
        uploaded_files = []
        for file in files:
            encode_file = encode_filename(file.filename)
            save_path = upload_folder + encode_file
            await save_content_to_local_disk(save_path, file)
            index = ingest_data_to_neo4j(
                DocPath(
                    path=save_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    process_table=process_table,
                    table_strategy=table_strategy,
                )
            )
            uploaded_files.append(save_path)
            if logflag:
                logger.info(f"Successfully saved file {save_path}")

    if link_list:
        link_list = json.loads(link_list)  # Parse JSON string to list
        if not isinstance(link_list, list):
            raise HTTPException(status_code=400, detail="link_list should be a list.")
        for link in link_list:
            encoded_link = encode_filename(link)
            save_path = upload_folder + encoded_link + ".txt"
            content = parse_html_new([link], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            try:
                await save_content_to_local_disk(save_path, content)
                index = ingest_data_to_neo4j(
                    DocPath(
                        path=save_path,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        process_table=process_table,
                        table_strategy=table_strategy,
                    )
                )
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Fail to ingest data")

            if logflag:
                logger.info(f"Successfully saved link {link}")

    if files or link_list:
        build_communities(index)
        result = {"status": 200, "message": "Data preparation succeeded"}
        if logflag:
            logger.info(result)
        return result
    else:
        raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


if __name__ == "__main__":
    opea_microservices["opea_service@extract_graph_neo4j"].start()
