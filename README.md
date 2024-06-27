<div align="center">

# Generative AI Examples

This project provides a collective list of Generative AI (GenAI) and Retrieval-Augmented Generation (RAG) examples such as chatbot with question and answering (ChatQnA), code generation (CodeGen), document summary (DocSum), etc.

[![version](https://img.shields.io/badge/release-0.6-green)](https://github.com/opea-project/GenAIExamples/releases)
[![license](https://img.shields.io/badge/license-Apache%202-blue)](https://github.com/intel/neural-compressor/blob/master/LICENSE)

---

<div align="left">

## GenAI Examples

All the examples are well-validated on Intel platforms. In addition, these examples are:

- <b>Easy to use</b>. Use ecosystem-compliant APIs to build the end-to-end GenAI examples

- <b>Easy to customize</b>. Customize the example using different framework, LLM, embedding, serving etc.

- <b>Easy to deploy</b>. Deploy the GenAI examples with performance on Intel platforms

> **Note**:
> The below support matrix gives the validated configurations. Feel free to customize per your needs.

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
			<td>Framework</td>
			<td>LLM</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/llava-hf/llava-1.5-7b-hf">LLaVA-1.5-7B</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
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
