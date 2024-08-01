<div align="center">

# Generative AI Examples

[![version](https://img.shields.io/badge/release-0.8-green)](https://github.com/opea-project/GenAIExamples/releases)
[![license](https://img.shields.io/badge/license-Apache%202-blue)](https://github.com/intel/neural-compressor/blob/master/LICENSE)

---

<div align="left">

## Introduction

GenAIComps-based Generative AI examples offer streamlined deployment, testing, and scalability. All examples are fully compatible with Docker and Kubernetes, supporting a wide range of hardware platforms such as Xeon, Gaudi, and GPUs.

## Architecture

GenAIExample utilizes all microservice components from GenAIComps. This approach allows for flexible, modular service deployment in cloud-native environments. 

GenAIInfra, part of the OPEA containerization and cloud-native suite, enables quick and efficient deployment of GenAIExamples in the cloud. 

GenAIEvals measures service performance metrics such as throughput, latency, and accuracy for GenAIExamples. This feature helps users compare performance across various hardware configurations easily.

The Architecture of OPEA is as below.

![architecture](./assets/2.png)

## Getting Started

GenAIExamples offers flexible deployment options that cater to different user needs, enabling efficient use and deployment in various environments. Here’s a brief overview of the three primary methods: Python startup, Docker Compose, and Kubernetes.

1. <b>Python Startup</b>: Allows developers to quickly test and modify GenAIExamples on their local machines.
2. <b>Docker Compose</b>: Utilizes a YAML file to manage multi-container Docker applications for GenAIExamples simultaneously.
3. <b>Kubernetes</b>: Orchestrates containers for efficient deployment of GenAIExamples across distributed environments.

Users can choose the most suitable approach based on ease of setup, scalability needs, and the environment in which they are operating.

### Prerequisites

| Startup Methods | Docker Compose            | Kubernetes |
|-----------------|---------------------------|------------|
| **Environment Prepare** | [Docker](#) |  [Xeon]() <br> [Gaudi](#)  |

### Deployment

<table>
    <tr>
        <th rowspan="3" style="text-align:center;">Use Cases</th>
        <th colspan="4" style="text-align:center;">Deployment</th>
    </tr>
    <tr>
        <td colspan="2" style="text-align:center;">Docker Compose</td>
        <td rowspan="2" style="text-align:center;">Kubernetes</td>
    </tr>
    <tr>
        <td style="text-align:center;">Xeon</td>
        <td style="text-align:center;">Gaudi</td>
    </tr>
    <tr>
        <td style="text-align:center;">ChatQnA</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/kubernetes/README.md">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">CodeGen</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeGen/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeGen/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeGen/kubernetes/README.md">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">CodeTrans</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeTrans/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeTrans/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeTrans/kubernetes/README.md">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">DocSum</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/DocSum/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/DocSum/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/DocSum/kubernetes/README.md">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">SearchQnA</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/SearchQnA/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/SearchQnA/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/SearchQnA/kubernetes/README.md">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">FaqGen</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/FaqGen/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/FaqGen/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/FaqGen/kubernetes/manifests/README.md">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">Translation</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/Translation/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/Translation/docker/gaudi/README.md">Gaudi Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/tree/main/Translation/kubernetes">K8s Link</a></td>
    </tr>
    <tr>
        <td style="text-align:center;">AudioQnA</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/AudioQnA/docker/xeon/README.md">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/blob/main/AudioQnA/docker/gaudi/README.md">Gaudi Link</a></td>
        <td>Not support yet</td>
    </tr>
    <tr>
        <td style="text-align:center;">VisualQnA</td>
        <td><a href="https://github.com/opea-project/GenAIExamples/tree/main/VisualQnA">Xeon Link</a></td>
        <td><a href="https://github.com/opea-project/GenAIExamples/tree/main/VisualQnA">Gaudi Link</a></td>
        <td>Not support yet</td>
    </tr>
</table>

## Benchmark

TBD

## Development Documents

TBD

## Support Examples

### ChatQnA

[ChatQnA](./ChatQnA/README.md) is an example of chatbot for question and answering through retrieval argumented generation (RAG).

<table>
	<tbody>
		<tr>
			<td>Framework</td>
			<td>LLM</td>
			<td>Embedding</td>
			<td>Vector Database</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://redis.io/">Redis</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon/Gaudi2/GPU</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://www.trychroma.com/">Chroma</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://redis.io/">Redis</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://qdrant.tech/">Qdrant</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/Qwen/Qwen2-7B">Qwen2-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://redis.io/">Redis</a></td>
			<td><a href=<a href="https://github.com/huggingface/text-embeddings-inference">TEI</td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
	</tbody>
</table>

### CodeGen

[CodeGen](./CodeGen/README.md) is an example of copilot designed for code generation in Visual Studio Code.

<table>
	<tbody>
		<tr>
			<td>Framework</td>
			<td>LLM</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/meta-llama/CodeLlama-7b-hf">meta-llama/CodeLlama-7b-hf</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Copilot</td>
		</tr>
	</tbody>
</table>

### CodeTrans

[CodeTrans](./CodeTrans/README.md) is an example of chatbot for converting code written in one programming language to another programming language while maintaining the same functionality.

<table>
	<tbody>
		<tr>
			<td>Framework</td>
			<td>LLM</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/HuggingFaceH4/mistral-7b-grok">HuggingFaceH4/mistral-7b-grok</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Code Translation</td>
		</tr>
	</tbody>
</table>

### DocSum

[DocSum](./DocSum/README.md) is an example of chatbot for summarizing the content of documents or reports.

<table>
	<tbody>
		<tr>
			<td>Framework</td>
			<td>LLM</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
	</tbody>
</table>

### Language Translation

[Language Translation](./Translation/README.md) is an example of chatbot for converting a source-language text to an equivalent target-language text.

<table>
	<tbody>
		<tr>
			<td>Framework</td>
			<td>LLM</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/haoranxu/ALMA-13B">haoranxu/ALMA-13B</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Language Translation</td>
		</tr>
	</tbody>
</table>

### SearchQnA

[SearchQnA](./SearchQnA/README.md) is an example of chatbot for using search engine to enhance QA quality.

<table>
	<tbody>
		<tr>
			<td>Framework</td>
			<td>LLM</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon/Gaudi2</td>
			<td>Chatbot</td>
		</tr>
	</tbody>
</table>

### VisualQnA

[VisualQnA](./VisualQnA/README.md) is an example of chatbot for question and answering based on the images.

<table>
	<tbody>
		<tr>
			<td>LLM</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://huggingface.co/llava-hf/llava-1.5-7b-hf">LLaVA-1.5-7B</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
	</tbody>
</table>

> **_NOTE:_** The `Language Translation`, `SearchQnA`, `VisualQnA` and other use cases not listing here are in active development. The code structure of these use cases are subject to change.

## Additional Content

- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Contribution](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
