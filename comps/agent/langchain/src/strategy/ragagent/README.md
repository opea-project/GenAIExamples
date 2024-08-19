# RAG Agent

This agent is specifically designed to improve answer quality over conventional RAG.
This agent strategy includes steps listed below:

1. QueryWriter
   This is an llm with tool calling capability, it decides if tool calls are needed to answer the user query or it can answer with llm's parametric knowledge.

   - Yes: Rephrase the query in the form of a tool call to the Retriever tool, and send the rephrased query to 'Retriever'. The rephrasing is important as user queries may be not be clear and simply using user query may not retrieve relevant documents.
   - No: Complete the query with Final answer

2. Retriever:

   - Get related documents from a retrieval tool, then send the documents to 'DocumentGrader'. Note: The retrieval tool here is broad-sense, which can be a text retriever over a proprietary knowledge base, a websearch API, knowledge graph API, SQL database API etc.

3. DocumentGrader
   Judge retrieved info relevance with respect to the user query

   - Yes: Go to TextGenerator
   - No: Go back to QueryWriter to rewrite query.

4. TextGenerator
   - Generate an answer based on query and last retrieved context.
   - After generation, go to END.

Note:

- Currently the performance of this RAG agent has been tested and validated with only one retrieval tool. If you want to use multiple retrieval tools, we recommend a hierarchical multi-agent system where a supervisor agent dispatches requests to multiple worker RAG agents, where individual worker RAG agents uses one type of retrieval tool.
- The max number of retrieves is set at 3.
- You can specify a small `recursion_limit` to stop early or a big `recursion_limit` to fully use the 3 retrieves.
- The TextGenerator only looks at the last retrieved docs.
