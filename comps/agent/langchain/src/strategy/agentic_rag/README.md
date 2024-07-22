# Agentic Rag

This strategy is a practise provided with [LangGraph](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag)
This agent strategy includes steps listed below:

1. RagAgent
   decide if this query need to get extra help

   - Yes: Goto 'Retriever'
   - No: Complete the query with Final answer

2. Retriever:

   - Get relative Info from tools, Goto 'DocumentGrader'

3. DocumentGrader
   Judge retrieved info relevance based query

   - Yes: Complete the query with Final answer
   - No: Goto 'Rewriter'

4. Rewriter
   Rewrite the query and Goto 'RagAgent'

![Agentic Rag Workflow](https://blog.langchain.dev/content/images/size/w1000/2024/02/image-16.png)
