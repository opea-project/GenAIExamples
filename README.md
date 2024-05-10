<div align="center">

# Generative AI Components (GenAIComps)

<p align="center">
<b>Build Enterprise-grade Generative AI applications with microservice architecture</b>
</p>

<div align="left">

This initiative empowers the development of high-quality Generative AI applications for enterprises via microservices, simplifying the scaling and deployment process for production. It abstracts away infrastructure complexities, facilitating the seamless development and deployment of Enterprise AI services.

## GenAIComps

GenAIComps provides a suite of microservices, leveraging a service composer to assemble a mega-service tailored for real-world Enterprise AI applications. All the microservices are containerized, allowing cloud native deployment. Checkout how the microservices are used in [GenAIExamples](https://github.com/opea-project/GenAIExamples)).

![Architecture](https://i.imgur.com/r5J0i8j.png)

## MicroService

The initially supported microservices are described in the below table. More microservices are on the way.

<table>
	<tbody>
		<tr>
			<td>MicroService</td>
            <td>Framework</td>
			<td>Model</td>
			<td>Serving</td>
			<td>HW</td>
			<td>Description</td>
		</tr>
		<tr>
			<td><a href="./comps/embeddings/README.md">Embedding</a></td>
            <td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-large-en-v1.5">BAAI/bge-large-en-v1.5</a></td>
			<td><a href="https://github.com/huggingface/tei-gaudi">TEI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Embedding on Gaudi2</td>
		</tr>
		<tr>
			<td><a href="./comps/embeddings/README.md">Embedding</a></td>
            <td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en-v1.5">BAAI/bge-base-en-v1.5</a></td>
			<td><a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon</td>
			<td>Embedding on Xeon CPU</td>
		</tr>
		<tr>
			<td><a href="./comps/retrievers/README.md">Retriever</a></td>
			<td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en-v1.5">BAAI/bge-base-en-v1.5</a></td>
			<td><a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon</td>
			<td>Retriever on Xeon CPU</td>
		</tr>
		<tr>
			<td><a href="./comps/reranks/README.md">Reranking</a></td>
            <td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-reranker-large">BAAI/bge-reranker-large</a></td>
			<td><a href="https://github.com/huggingface/tei-gaudi">TEI-Habana</a></td>
			<td>Gaudi2</td>
			<td>Reranking on Gaudi2</td>
		</tr>
		<tr>
			<td><a href="./comps/reranks/README.md">Reranking</a></td>
            <td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-reranker-base">BBAAI/bge-reranker-base</a></td>
			<td><a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon</td>
			<td>Reranking on Xeon CPU</td>
		</tr>
		<tr>
			<td><a href="./comps/llms/README.md">LLM</a></td>
            <td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">Intel/neural-chat-7b-v3-3</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI Gaudi</a></td>
			<td>Gaudi2</td>
			<td>LLM on Gaudi2</td>
		</tr>
		<tr>
			<td><a href="./comps/llms/README.md">LLM</a></td>
            <td><a href="https://www.langchain.com">LangChain</a></td>
			<td><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">Intel/neural-chat-7b-v3-3</a></td>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon</td>
			<td>LLM on Xeon CPU</td>
		</tr>
	</tbody>
</table>

## MegaService (under construction)

## Additional Content

- [Contribution](/CONTRIBUTING.md)
- [Legal Information](/LEGAL_INFORMATION.md)
- [Security Policy](/SECURITY.md)
