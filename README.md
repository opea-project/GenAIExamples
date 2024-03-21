# Intel Generative AI Examples

## Introduction

This project provides a collective list of Generative AI (GenAI) examples such as chatbot with question and answering (ChatQnA), code generation, document summary, etc. The examples are developed by leveraging the ecosystem components with Intel optimizations, therefore delivering the high perforamnce on Intel platforms. 

## GenAI Examples

### ChatQnA

[ChatQnA](./ChatQnA/README.md) is an example of chatbot with question and answering through retrieval argumented generation (RAG).


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
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-1">NeuralChat-v3</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://redis.io/">Redis</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-1">NeuralChat-v3</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
			<td><a href="https://www.trychroma.com/">Chroma</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
	</tbody>
</table>


### CodeGen
[CodeGen](./CodeGen/README.md) is a copilot application designed for code generation use case. We offer a VS Code plugin for easy usage. In this example, we demonstrate how code generation can be efficiently executed on the Intel Gaudi2 platform.


### DocSum
[DocSum](./DocSum/README.md) is a chatbot for summarizing the content of your documents or reports. The example is developed with Langchain API and deployed on Gaudi through Hugging Face text generation inference (TGI) serving.

### VisualQnA
[VisualQnA](./VisualQnA/README.md) is a chatbot for visual question and answering task. This example guides you through how to deploy a [LLaVA](https://llava-vl.github.io/) (Large Language and Vision Assistant) model on Intel Gaudi2.
