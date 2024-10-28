# GraphRAG Standalone

Monolithic front-end/back-end example of GraphRAG using the SEC Edgar sample dataset.

## Getting started - non-container development

There are two services:

1. api - using langserve
2. ui - streamlit app

### Configure environment

1. Make a copy of the example env file: `cp env-example .env`
2. Modify the dot env with Neo4j credentials and OpenAI API key
  - the `GOOGLE_MAPS_API_KEY` is only needed during data preparation

### Start API

- `cd api`
- ..?

## Data Preparation

Data preparation is a manual process, directly creating a knowledge graph from example structured
and unstructured data contained in the `data` directory.

See the `notebooks/data-prep.ipynb` for data preparation.

*NOTE*: The data has a quality issue, where Apple Inc has been misidentified by the identity mapping!

This is great! The data quality issue is easy to notice and fix within a knowledge graph, because the
structured and unstructured data are all connected, making it easy to explore, debug and curate.
