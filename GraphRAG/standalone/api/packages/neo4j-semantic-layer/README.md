# neo4j-semantic-layer for SEC Edgar

The semantic layer equips the agent with a suite of robust tools, allowing it to interact with the graph databas based on the user's intent.

## Tools

The agent utilizes several tools to interact with the Neo4j graph database effectively:

1. **Company tool**:
   - Retrieves information about a company based on their 10-K, ensuring the agent has access to the latest and most relevant information.
2. **Cypher Tool**:
   - Provides movie recommendations based upon user preferences and input.

## Environment Setup

You need to define the following environment variables

```
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
NEO4J_URI=<YOUR_NEO4J_URI>
NEO4J_USERNAME=<YOUR_NEO4J_USERNAME>
NEO4J_PASSWORD=<YOUR_NEO4J_PASSWORD>
```

