# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import sys

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../")
sys.path.append(comps_path)
import json

import requests
from langchain import hub
from langchain.agents import AgentExecutor, Tool, load_tools
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActJsonSingleInputOutputParser
from langchain.chains import GraphCypherQAChain, RetrievalQA
from langchain.tools.render import render_text_description
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.graphs import Neo4jGraph
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.vectorstores.neo4j_vector import Neo4jVector

from comps import GeneratedDoc, GraphDoc, ServiceType, opea_microservices, register_microservice


def get_retriever(input, neo4j_endpoint, neo4j_username, neo4j_password, llm):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vector_index = Neo4jVector.from_existing_graph(
        embeddings,
        url=neo4j_endpoint,
        username=neo4j_username,
        password=neo4j_password,
        index_name=input.rag_index_name,
        node_label=input.rag_node_label,
        text_node_properties=input.rag_text_node_properties,
        embedding_node_property=input.rag_embedding_node_property,
    )
    vector_qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vector_index.as_retriever())
    return vector_qa


def get_cypherchain(graph, cypher_llm, qa_llm):
    graph.refresh_schema()
    cypher_chain = GraphCypherQAChain.from_llm(cypher_llm=cypher_llm, qa_llm=qa_llm, graph=graph, verbose=True)
    return cypher_chain


def get_agent(vector_qa, cypher_chain, llm_repo_id):
    # define two tools
    tools = [
        Tool(
            name="Tasks",
            func=vector_qa.invoke,
            description="""Useful when you need to answer questions about descriptions of tasks.
            Not useful for counting the number of tasks.
            Use full question as input.
            """,
        ),
        Tool(
            name="Graph",
            func=cypher_chain.invoke,
            description="""Useful when you need to answer questions about microservices,
            their dependencies or assigned people. Also useful for any sort of
            aggregation like counting the number of tasks, etc.
            Use full question as input.
            """,
        ),
    ]

    # setup ReAct style prompt
    prompt = hub.pull("hwchase17/react-json")
    prompt = prompt.partial(
        tools=render_text_description(tools),
        tool_names=", ".join([t.name for t in tools]),
    )

    # define chat model
    llm = HuggingFaceEndpoint(repo_id=llm_repo_id, max_new_tokens=512)
    chat_model = ChatHuggingFace(llm=llm)
    chat_model_with_stop = chat_model.bind(stop=["\nObservation"])

    # define agent
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        }
        | prompt
        | chat_model_with_stop
        | ReActJsonSingleInputOutputParser()
    )

    # instantiate AgentExecutor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor


@register_microservice(
    name="opea_service@knowledge_graph",
    endpoint="/v1/graphs",
    host="0.0.0.0",
    port=8060,
)
def graph_query(input: GraphDoc) -> GeneratedDoc:
    print(input)

    ## Connect to Neo4j
    neo4j_endpoint = os.getenv("NEO4J_ENDPOINT", "neo4j://localhost:7687")
    neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j")
    graph = Neo4jGraph(url=neo4j_endpoint, username=neo4j_username, password=neo4j_password)

    ## keep for multiple tests, will remove later
    graph.query("MATCH (n) DETACH DELETE n")
    import_query = json.load(open("data/microservices.json", "r"))["query"]
    graph.query(import_query)

    ## get tool flag
    flag_agent = True if input.strtype == "query" else False
    flag_rag = True if input.strtype in ["query", "rag"] else False

    ## define LLM
    if flag_agent or flag_rag:
        llm_endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:8080")
        llm = HuggingFaceEndpoint(
            endpoint_url=llm_endpoint,
            timeout=600,
            max_new_tokens=input.max_new_tokens,
        )

    ## define a retriever
    if flag_rag:
        vector_qa = get_retriever(input, neo4j_endpoint, neo4j_username, neo4j_password, llm)

    ## define an agent
    if flag_agent:
        llm_repo_id = os.getenv("AGENT_LLM", "HuggingFaceH4/zephyr-7b-beta")
        cypher_chain = get_cypherchain(graph, llm, llm)  # define a cypher generator
        agent_executor = get_agent(vector_qa, cypher_chain, llm_repo_id)

    ## process input query
    if input.strtype == "cypher":
        result_dicts = graph.query(input.text)
        result = ""
        for result_dict in result_dicts:
            for key in result_dict:
                result += str(key) + ": " + str(result_dict[key])
    elif input.strtype == "rag":
        result = vector_qa.invoke(input.text)["result"]
    elif input.strtype == "query":
        result = agent_executor.invoke({"input": input.text})["output"]
    else:
        result = "Please specify strtype as one of cypher, rag, query."
    return GeneratedDoc(text=result, prompt=input.text)


if __name__ == "__main__":
    opea_microservices["opea_service@knowledge_graph"].start()
