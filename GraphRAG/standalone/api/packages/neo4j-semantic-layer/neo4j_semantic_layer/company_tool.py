import os

from langchain_core.tools import create_retriever_tool
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'


company_info_cypher = """
MATCH (node)-[:PART_OF]->(f:Form),
    (f)<-[:FILED]-(com:Company),
    (com)<-[owns:OWNS_STOCK_IN]-(mgr:Manager)
WITH node, score, mgr, owns, com 
    ORDER BY owns.shares DESC LIMIT 10
WITH collect (
    mgr.name + 
    " owns " + owns.shares + " of " + com.name + 
    " at a value of $" + apoc.number.format(owns.value) + "." 
) AS investment_statements, com, node, score
RETURN 
    "Investors in " + com.name + " include...\n" +
    apoc.text.join(investment_statements, "\n") + 
    "\n" + 
    "Information about " + com.name + " that is relevant to the user question...\n" + node.text AS text,
    score,
    { 
      source: node.source
    } as metadata
"""

embeddings_api = OpenAIEmbeddings()

neo4j_vector_store = Neo4jVector.from_existing_graph(
    embedding=embeddings_api,
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    index_name="form_10k_chunks",
    node_label="Chunk",
    text_node_properties=["text"],
    embedding_node_property="textEmbedding",
    retrieval_query=company_info_cypher,
)
# Create a retriever from the vector store
company_retriever = neo4j_vector_store.as_retriever()

company_tool = create_retriever_tool(
    name="company_retriever",
    retriever=company_retriever,
    description="Search and return information about something....",
)
