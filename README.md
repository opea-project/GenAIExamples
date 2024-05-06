<div align="center">

# Generative AI Examples

This project provides a collective list of Generative AI (GenAI) and Retrieval-Augmented Generation (RAG) examples such as chatbot with question and answering (ChatQnA), code generation (CodeGen), document summary (DocSum), etc.

[![version](https://img.shields.io/badge/release-0.1-green)](https://github.com/opea-project/GenAIExamples/releases)
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://redis.io/">Redis</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://www.trychroma.com/">Chroma</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://redis.io/">Redis</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://qdrant.tech/">Qdrant</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/deepseek-ai/deepseek-coder-33b-instruct">Deepseek-Coder-33B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/HuggingFaceH4/mistral-7b-grok">HuggingFaceH4/mistral-7b-grok</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/haoranxu/ALMA-13B">haoranxu/ALMA-13B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
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
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/llava-hf/llava-1.5-7b-hf">LLaVA-1.5-7B</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
	</tbody>
</table>

## Additional Content

- [Contribution](/CONTRIBUTING.md)
- [Legal Information](/LEGAL_INFORMATION.md)
- [Security Policy](/SECURITY.md)
