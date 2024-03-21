# Intel Generative AI Examples

## Introduction

This project provides a collective list of Generative AI (GenAI) examples such as chatbot with question and answering (ChatQnA), code generation, document summary, etc. The examples are developed by leveraging the ecosystem components with Intel optimizations, therefore delivering the high perforamnce on Intel platforms. 

## GenAI Examples

### ChatQnA

[ChatQnA](./ChatQnA/README.md) is an example of chatbot with question and answering through retrieval argumented generation (RAG).


<table>
	<tbody>
		<tr>
			<td colspan="2">Framework</td>
			<td colspan="2">LLM</td>
			<td colspan="2">Embedding</td>
			<td colspan="2">Vector Database</td>
			<td colspan="2">Serving</td>
			<td colspan="2">HW</td>
			<td colspan="2">Description</td>
		</tr>
		<tr>
			<td>[angChain](https://www.langchain.com/)</td>
			<td>[NeuralChat-v3](https://huggingface.co/Intel/neural-chat-7b-v3-1)</td>
			<td>[BGE-Base](https://huggingface.co/BAAI/bge-base-en)</td>
			<td>[Redis](https://redis.io/)</td>
			<td>[TGI-Habana](https://github.com/huggingface/tgi-gaudi)</td>
			<td>Gaudi2</td>
			<td>Chatbot</td>
		</tr>
		<tr>
			<td>[angChain](https://www.langchain.com/)</td>
			<td>[NeuralChat-v3](https://huggingface.co/Intel/neural-chat-7b-v3-1)</td>
			<td>[BGE-Base](https://huggingface.co/BAAI/bge-base-en)</td>
			<td>[Chroma](https://www.trychroma.com/)</td>
			<td>[TGI-Habana](https://github.com/huggingface/tgi-gaudi)</td>
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
