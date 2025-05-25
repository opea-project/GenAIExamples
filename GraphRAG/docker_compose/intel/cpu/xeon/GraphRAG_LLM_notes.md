# About GraphRAG LLMs

## Overview
This GraphRAG app uses three distinct LLMs, each optimized for different tasks in the pipeline:
1. Dataprep LLM (endpoint)
2. Retriever LLM (endpoint)
3. Final LLM (cpu)

It also uses an embedding service that runs on CPU.

## 1. Dataprep LLM
Used during data ingestion phase to:
- Process and understand document structure
- Extract entities and relationships between entities 
- Generate and store community summaries in Neo4j 

[dataprep code that build communities and summarizes](https://github.com/opea-project/GenAIComps/blob/main/comps/dataprep/src/integrations/neo4j_llamaindex.py#L94):

**Key Requirements:**
- High-quality model for accurate relationship understanding.
- Larger context window for document processing
- Can be slower since it's one-time processing


## 2. Retriever LLM
Used during retrieval to:
- Evaluate relevance of the query to pre-computed community summaries (auery focused summarization)
- Generate specific answers from relevant communities
- Process multiple communities in parallel

[retriever code](https://github.com/opea-project/GenAIComps/blob/main/comps/retrievers/src/integrations/neo4j.py):

**Key Requirements:**
- Fast inference for real-time processing
- Efficient batch processing capabilities
- Balance between quality and speed


## 3. Final LLM
Used as the last step to:
- Process all retriever-generated answers
- Synthesize information from multiple communities
- Generate coherent final response

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