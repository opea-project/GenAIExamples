# DocRetriever Application

DocRetriever are the most widely adopted use case for leveraging the different methodologies to match user query against a set of free-text records. DocRetriever is essential to RAG system, which bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. The core of this architecture are vector databases, which are instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

## We provided DocRetriever with different deployment infra

- [docker xeon version](docker/xeon/) => minimum endpoints, easy to setup
- [docker gaudi version](docker/gaudi/) => with extra tei_gaudi endpoint, faster
