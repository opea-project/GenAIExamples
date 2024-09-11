# Dataprep Microservice

The Dataprep Microservice aims to preprocess the data from various sources (either structured or unstructured data) to text data, and convert the text data to embedding vectors then store them in the database.

## Install Requirements

```bash
apt-get update
apt-get install libreoffice
```

## Use LVM (Large Vision Model) for Summarizing Image Data

Occasionally unstructured data will contain image data, to convert the image data to the text data, LVM can be used to summarize the image. To leverage LVM, please refer to this [readme](../lvms/README.md) to start the LVM microservice first and then set the below environment variable, before starting any dataprep microservice.

```bash
export SUMMARIZE_IMAGE_VIA_LVM=1
```

## Dataprep Microservice with Redis

For details, please refer to this [readme](redis/README.md)

## Dataprep Microservice with Milvus

For details, please refer to this [readme](milvus/langchain/README.md)

## Dataprep Microservice with Qdrant

For details, please refer to this [readme](qdrant/langchain/README.md)

## Dataprep Microservice with Pinecone

For details, please refer to this [readme](pinecone/langchain/README.md)

## Dataprep Microservice with PGVector

For details, please refer to this [readme](pgvector/langchain/README.md)

## Dataprep Microservice with VDMS

For details, please refer to this [readme](vdms/README.md)

## Dataprep Microservice with Multimodal

For details, please refer to this [readme](multimodal/redis/langchain/README.md)
