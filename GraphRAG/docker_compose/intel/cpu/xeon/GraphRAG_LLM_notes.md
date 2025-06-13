# About GraphRAG LLMs

## Overview

GraphRAG uses three distinct LLMs, each optimized for different tasks in the pipeline:

1. Dataprep LLM
2. Retriever LLM
3. Final LLM

## 1. Dataprep LLM

Used during data ingestion phase to:

- Process and understand document structure
- Extract entities and relationships between entities
- Generate and store community summaries in Neo4j:

```python
# neo4j_llamaindex.py
async def generate_community_summary(self, text):
    """Generate summary for a given text using an LLM."""
    messages = [
        ChatMessage(
            role="system",
            content=(
                "You are provided with a set of relationships from a knowledge graph... "
                "Your task is to create a summary of these relationships..."
            ),
        )
    ]
    response = await self.llm.achat(trimmed_messages)
```

**Key Requirements:**

- High-quality model for accurate relationship understanding
- Larger context window for document processing
- Can be slower since it's one-time processing

## 2. Retriever LLM

Used during query processing to:

- Evaluate relevance of pre-computed community summaries
- Generate specific answers from relevant communities
- Process multiple communities in parallel

```python
def generate_answer_from_summary(self, community_summary, query):
    """Generate an answer from a community summary based on a given query using LLM."""
    prompt = (
        f"Given the community summary: {community_summary}, "
        f"how would you answer the following query? Query: {query}"
    )
    response = self._llm.chat(messages)
```

**Key Requirements:**

- Fast inference for real-time processing
- Efficient batch processing capabilities
- Balance between quality and speed

## 3. Final LLM

Used as the last step to:

- Process all retriever-generated answers
- Synthesize information from multiple communities
- Generate coherent final response

```python
# In graphrag.py
llm = MicroService(
    name="llm",
    host=LLM_SERVER_HOST_IP,
    port=LLM_SERVER_PORT,
    endpoint="/v1/chat/completions",
    service_type=ServiceType.LLM,
)
```

**Key Requirements:**

- Good at synthesizing multiple sources
- Strong natural language generation
- Maintains context across multiple inputs

## Data Flow

1. **Ingestion Phase**

   - Documents → Dataprep LLM → Community Summaries
   - Summaries stored in Neo4j

2. **Query Phase**
   - Query → Retriever LLM → Individual Community Answers
   - Answers → Final LLM → Coherent Response

## Configuration

Each LLM can be configured independently through environment variables:

- `DATAPREP_LLM_ENDPOINT` and `DATAPREP_LLM_MODEL_ID`
- `RETRIEVER_LLM_ENDPOINT` and `RETRIEVER_LLM_MODEL_ID`
- `FINAL_LLM_ENDPOINT` and `FINAL_LLM_MODEL_ID`

This allows for optimization of each LLM for its specific task in the pipeline.
