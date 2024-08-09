<div align="center">

# Supported Examples

<div align="left">

This document introduces the supported examples of GenAIExamples. The supported Vector Database, LLM models, serving frameworks and hardwares are listed as below.

## ChatQnA

[ChatQnA](./ChatQnA/README.md) is an example of chatbot for question and answering through retrieval augmented generation (RAG).

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
