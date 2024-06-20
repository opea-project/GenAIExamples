# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

from langchain_community.graphs import Neo4jGraph

neo4j_endpoint = os.getenv("NEO4J_ENDPOINT", "neo4j://localhost:7687")
neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j")
graph = Neo4jGraph(url=neo4j_endpoint, username=neo4j_username, password=neo4j_password)

# remove all nodes
graph.query("MATCH (n) DETACH DELETE n")

# ingest
import_query = json.load(open("data/microservices.json", "r"))["query"]
graph.query(import_query)
print("Total nodes: ", graph.query("MATCH (n) RETURN count(n)"))
print("Total edges: ", graph.query("MATCH ()-->() RETURN count(*)"))
