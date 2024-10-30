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

from comps import CustomLogger, DocPath, opea_microservices, register_microservice
from comps.dataprep.utils import (
    document_loader,
    encode_filename,
    get_separators,
    get_tables_result,
    parse_html,
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
    max_cluster_size = 5

    def __init__(self, username: str, password: str, url: str, llm: LLM):
        super().__init__(username=username, password=password, url=url)
        self.llm = llm

    def generate_community_summary(self, text):
        """Generate summary for a given text using an LLM."""
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
        if OPENAI_API_KEY:
            response = OpenAI().chat(messages)
        else:
            response = self.llm.chat(messages)

        clean_response = re.sub(r"^assistant:\s*", "", str(response)).strip()
        return clean_response

    def build_communities(self):
        """Builds communities from the graph and summarizes them."""
        nx_graph = self._create_nx_graph()
        community_hierarchical_clusters = hierarchical_leiden(nx_graph, max_cluster_size=self.max_cluster_size)
        self.entity_info, community_info = self._collect_community_info(nx_graph, community_hierarchical_clusters)
        self._summarize_communities(community_info)

    def _create_nx_graph(self):
        """Converts internal graph representation to NetworkX graph."""
        nx_graph = nx.Graph()
        triplets = self.get_triplets()
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

    def _summarize_communities(self, community_info):
        """Generate and store summaries for each community."""
        for community_id, details in community_info.items():
            details_text = "\n".join(details) + "."  # Ensure it ends with a period
            self.community_summary[community_id] = self.generate_community_summary(details_text)

            # To store summaries in neo4j
            # summary = self.generate_community_summary(details_text)
            # self.community_summary[
            #     community_id
            # ] = self.store_community_summary_in_neo4j(community_id, summary)

    def store_community_summary_in_neo4j(self, community_id, summary):
        """Store the community summary in Neo4j."""
        with driver.session() as session:
            session.run(
                """
                MERGE (c:Community {id: $community_id})
                SET c.summary = $summary
            """,
                community_id=community_id,
                summary=summary,
            )

    def get_community_summaries(self):
        """Returns the community summaries, building them if not already done."""
        if not self.community_summary:
            self.build_communities()
        return self.community_summary

    def query_community_summaries(self):
        """Query and print community summaries from Neo4j."""
        with driver.session() as session:
            result = session.run(
                """
                MATCH (c:Community)
                RETURN c.id AS community_id, c.summary AS summary
            """
            )
            for record in result:
                print(f"Community ID: {record['community_id']}")
                print(f"Community Summary: {record['summary']}")

    def query_schema(self):
        """Query and print the schema information from Neo4j."""
        with driver.session() as session:
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
        max_paths_per_chunk: int = 10,
        num_workers: int = 4,
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


def inspect_db():
    try:
        with driver.session() as session:
            # Check for property keys
            result = session.run("CALL db.propertyKeys()")
            property_keys = [record["propertyKey"] for record in result]
            print("Property Keys:", property_keys)

            # Check for node labels
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            print("Node Labels:", labels)

            # Check for relationship types
            result = session.run("CALL db.relationshipTypes()")
            relationship_types = [record["relationshipType"] for record in result]
            print("Relationship Types:", relationship_types)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()


def parse_fn(response_str: str) -> Any:
    entities = re.findall(entity_pattern, response_str)
    relationships = re.findall(relationship_pattern, response_str)
    if logflag:
        logger.info(f"len of parsed entities: {len(entities)} and relationships: {len(relationships)}")
    return entities, relationships


def get_model_name_from_tgi_endpoint(url):
    try:
        response = requests.get(f"{url}/info")
        response.raise_for_status()  # Ensure we notice bad responses
        try:
            model_info = response.json()
            model_name = model_info.get("model_id")
            if model_name:
                return model_name
            else:
                logger.error(f"model_id not found in the response from {url}")
                return None
        except ValueError:
            logger.error(f"Invalid JSON response from {url}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request to {url} failed: {e}")
        return None


logger = CustomLogger("prepare_doc_neo4j")
logflag = os.getenv("LOGFLAG", False)

upload_folder = "./uploaded_files/"
driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
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
        llm_name = get_model_name_from_tgi_endpoint(TGI_LLM_ENDPOINT)
        llm = TextGenerationInference(
            model_url=TGI_LLM_ENDPOINT,
            model_name=llm_name,
            temperature=0.7,
            max_tokens=1512,  # 512otherwise too shor
        )
        emb_name = get_model_name_from_tgi_endpoint(TEI_EMBEDDING_ENDPOINT)
        embed_model = TextEmbeddingsInference(
            base_url=TEI_EMBEDDING_ENDPOINT,
            model_name=emb_name,
            timeout=60,  # timeout in seconds
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
    inspect_db()
    if logflag:
        logger.info(f"Total number of triplets {len(index.property_graph_store.get_triplets())}")

    # index.property_graph_store.build_communities()
    # print("done building communities")

    if logflag:
        logger.info("The graph is built.")

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
            ingest_data_to_neo4j(
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
        result = {"status": 200, "message": "Data preparation succeeded"}
        if logflag:
            logger.info(result)
        return result

    if link_list:
        link_list = json.loads(link_list)  # Parse JSON string to list
        if not isinstance(link_list, list):
            raise HTTPException(status_code=400, detail="link_list should be a list.")
        for link in link_list:
            encoded_link = encode_filename(link)
            save_path = upload_folder + encoded_link + ".txt"
            content = parse_html([link])[0][0]
            try:
                await save_content_to_local_disk(save_path, content)
                ingest_data_to_neo4j(
                    DocPath(
                        path=save_path,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        process_table=process_table,
                        table_strategy=table_strategy,
                    )
                )
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Fail to ingest data into qdrant.")

            if logflag:
                logger.info(f"Successfully saved link {link}")

        result = {"status": 200, "message": "Data preparation succeeded"}
        if logflag:
            logger.info(result)
        return result

    raise HTTPException(status_code=400, detail="Must provide either a file or a string list.")


if __name__ == "__main__":
    opea_microservices["opea_service@extract_graph_neo4j"].start()
