# Supported Examples

This document introduces the supported examples of GenAIExamples. The supported Vector Database, LLM models, serving frameworks and hardwares are listed as below.

## ChatQnA

[ChatQnA](./ChatQnA/README.md) is an example of chatbot for question and answering through retrieval augmented generation (RAG).

| Framework                                                                      | LLM                                                               | Embedding                                           | Vector Database                      | Serving                                                                                                                         | HW              | Description |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | --------------- | ----------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [NeuralChat-7B](https://huggingface.co/Intel/neural-chat-7b-v3-3) | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Redis](https://redis.io/)           | [TGI](https://github.com/huggingface/text-generation-inference) [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon/Gaudi2/GPU | Chatbot     |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [NeuralChat-7B](https://huggingface.co/Intel/neural-chat-7b-v3-3) | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Chroma](https://www.trychroma.com/) | [TGI](https://github.com/huggingface/text-generation-inference) [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon/Gaudi2     | Chatbot     |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Mistral-7B](https://huggingface.co/mistralai/Mistral-7B-v0.1)    | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Redis](https://redis.io/)           | [TGI](https://github.com/huggingface/text-generation-inference) [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon/Gaudi2     | Chatbot     |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Mistral-7B](https://huggingface.co/mistralai/Mistral-7B-v0.1)    | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Qdrant](https://qdrant.tech/)       | [TGI](https://github.com/huggingface/text-generation-inference) [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon/Gaudi2     | Chatbot     |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Qwen2-7B](https://huggingface.co/Qwen/Qwen2-7B)                  | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Redis](https://redis.io/)           | [TEI](https://github.com/huggingface/text-embeddings-inference)                                                                 | Xeon/Gaudi2     | Chatbot     |

### CodeGen

[CodeGen](./CodeGen/README.md) is an example of copilot designed for code generation in Visual Studio Code.

| Framework                                                                      | LLM                                                                             | Serving                                                         | HW          | Description |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ----------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [meta-llama/CodeLlama-7b-hf](https://huggingface.co/meta-llama/CodeLlama-7b-hf) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Copilot     |

### CodeTrans

[CodeTrans](./CodeTrans/README.md) is an example of chatbot for converting code written in one programming language to another programming language while maintaining the same functionality.

| Framework                                                                      | LLM                                                                                   | Serving                                                         | HW          | Description      |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ---------------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [HuggingFaceH4/mistral-7b-grok](https://huggingface.co/HuggingFaceH4/mistral-7b-grok) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Code Translation |

### DocSum

[DocSum](./DocSum/README.md) is an example of chatbot for summarizing the content of documents or reports.

| Framework                                                                      | LLM                                                               | Serving                                                         | HW          | Description |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ----------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [NeuralChat-7B](https://huggingface.co/Intel/neural-chat-7b-v3-3) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Chatbot     |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Mistral-7B](https://huggingface.co/mistralai/Mistral-7B-v0.1)    | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Chatbot     |

### Language Translation

[Language Translation](./Translation/README.md) is an example of chatbot for converting a source-language text to an equivalent target-language text.

| Framework                                                                      | LLM                                                           | Serving                                                         | HW          | Description          |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | -------------------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [haoranxu/ALMA-13B](https://huggingface.co/haoranxu/ALMA-13B) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Language Translation |

### SearchQnA

[SearchQnA](./SearchQnA/README.md) is an example of chatbot for using search engine to enhance QA quality.

| Framework                                                                      | LLM                                                               | Serving                                                         | HW          | Description |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ----------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [NeuralChat-7B](https://huggingface.co/Intel/neural-chat-7b-v3-3) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Chatbot     |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Mistral-7B](https://huggingface.co/mistralai/Mistral-7B-v0.1)    | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Chatbot     |

### VisualQnA

[VisualQnA](./VisualQnA/README.md) is an example of chatbot for question and answering based on the images.

| LLM                                                             | HW     | Description |
| --------------------------------------------------------------- | ------ | ----------- |
| [LLaVA-1.5-7B](https://huggingface.co/llava-hf/llava-1.5-7b-hf) | Gaudi2 | Chatbot     |

> **_NOTE:_** The `Language Translation`, `SearchQnA`, `VisualQnA` and other use cases not listing here are in active development. The code structure of these use cases are subject to change.
