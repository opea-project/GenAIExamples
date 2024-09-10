# VLLM Endpoint Service

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products). This guide provides an example on how to launch vLLM serving endpoint on CPU and Gaudi accelerators.

## Embeddings Microservice with TEI

We support both `langchain` and `llama_index` for TEI serving.

For details, please refer to [langchain readme](langchain/tei/README.md) or [llama index readme](llama_index/tei/README.md).

## Embeddings Microservice with Mosec

For details, please refer to this [readme](langchain/mosec/README.md).

## Embeddings Microservice with Neural Speed

For details, please refer to this [readme](neural-speed/README.md).

## Embeddings Microservice with Multimodal Clip

For details, please refer to this [readme](multimodal_clip/README.md).

## Embeddings Microservice with Multimodal Langchain

For details, please refer to this [readme](multimodal_embeddings/README.md).
