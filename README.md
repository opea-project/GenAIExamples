<div align="center">

# Generative AI Components (GenAIComps)

<p align="center">
<b>Build Enterprise-grade Generative AI Applications with Microservice Architecture</b>
</p>

<div align="left">

This initiative empowers the development of high-quality Generative AI applications for enterprises via microservices, simplifying the scaling and deployment process for production. It abstracts away infrastructure complexities, facilitating the seamless development and deployment of Enterprise AI services.

## GenAIComps

GenAIComps provides a suite of microservices, leveraging a service composer to assemble a mega-service tailored for real-world Enterprise AI applications. All the microservices are containerized, allowing cloud native deployment. Checkout how the microservices are used in [GenAIExamples](https://github.com/opea-project/GenAIExamples).

![Architecture](https://i.imgur.com/r5J0i8j.png)

### Installation

- Install from Pypi

```bash
pip install opea-comps
```

- Build from Source

```bash
git clone https://github.com/opea-project/GenAIComps
cd GenAIComps
pip install -e .
```

## MicroService

`Microservices` are akin to building blocks, offering the fundamental services for constructing `RAG (Retrieval-Augmented Generation)` applications.

Each `Microservice` is designed to perform a specific function or task within the application architecture. By breaking down the system into smaller, self-contained services, `Microservices` promote modularity, flexibility, and scalability.

This modular approach allows developers to independently develop, deploy, and scale individual components of the application, making it easier to maintain and evolve over time. Additionally, `Microservices` facilitate fault isolation, as issues in one service are less likely to impact the entire system.

The initially supported `Microservices` are described in the below table. More `Microservices` are on the way.

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
			<td rowspan="2"><a href="./comps/embeddings/README.md">Embedding</a></td>
            <td rowspan="2"><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td rowspan="2"><a href="https://huggingface.co/BAAI/bge-large-en-v1.5">BAAI/bge-large-en-v1.5</a></td>
			<td><a href="https://github.com/huggingface/tei-gaudi">TEI-Gaudi</a></td>
			<td>Gaudi2</td>
			<td>Embedding on Gaudi2</td>
		</tr>
		<tr>
			<td><a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon</td>
			<td>Embedding on Xeon CPU</td>
		</tr>
		<tr>
			<td><a href="./comps/retrievers/README.md">Retriever</a></td>
			<td><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td><a href="https://huggingface.co/BAAI/bge-base-en-v1.5">BAAI/bge-base-en-v1.5</a></td>
			<td><a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon</td>
			<td>Retriever on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="2"><a href="./comps/reranks/README.md">Reranking</a></td>
            <td rowspan="2"><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td ><a href="https://huggingface.co/BAAI/bge-reranker-large">BAAI/bge-reranker-large</a></td>
			<td><a href="https://github.com/huggingface/tei-gaudi">TEI-Gaudi</a></td>
			<td>Gaudi2</td>
			<td>Reranking on Gaudi2</td>
		</tr>
		<tr>
			<td><a href="https://huggingface.co/BAAI/bge-reranker-base">BBAAI/bge-reranker-base</a></td>
			<td><a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
			<td>Xeon</td>
			<td>Reranking on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="2"><a href="./comps/asr/README.md">ASR</a></td>
            <td rowspan="2">NA</a></td>
			<td rowspan="2"><a href="https://huggingface.co/openai/whisper-small">openai/whisper-small</a></td>
			<td rowspan="2">NA</td>
			<td>Gaudi2</td>
			<td>Audio-Speech-Recognition on Gaudi2</td>
		</tr>
		<tr>
			<td>Xeon</td>
			<td>Audio-Speech-RecognitionS on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="2"><a href="./comps/tts/README.md">TTS</a></td>
            <td rowspan="2">NA</a></td>
			<td rowspan="2"><a href="https://huggingface.co/microsoft/speecht5_tts">microsoft/speecht5_tts</a></td>
			<td rowspan="2">NA</td>
			<td>Gaudi2</td>
			<td>Text-To-Speech on Gaudi2</td>
		</tr>
		<tr>
			<td>Xeon</td>
			<td>Text-To-Speech on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="4"><a href="./comps/dataprep/README.md">Dataprep</a></td>
            <td rowspan="2"><a href="https://qdrant.tech/">Qdrant</td>
			<td rowspan="2"><a href="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2">sentence-transformers/all-MiniLM-L6-v2</a></td>
			<td rowspan="4">NA</td>
			<td>Gaudi2</td>
			<td>Dataprep on Gaudi2</td>
		</tr>
		<tr>
			<td>Xeon</td>
			<td>Dataprep on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="2"><a href="https://redis.io/">Redis</td>
			<td rowspan="2"><a href="https://huggingface.co/BAAI/bge-base-en-v1.5">BAAI/bge-base-en-v1.5</a></td>
			<td>Gaudi2</td>
			<td>Dataprep on Gaudi2</td>
		</tr>
		<tr>
			<td>Xeon</td>
			<td>Dataprep on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="6"><a href="./comps/llms/README.md">LLM</a></td>
            <td rowspan="6"><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai">LlamaIndex</a></td>
			<td rowspan="2"><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">Intel/neural-chat-7b-v3-3</a></td>
			<td><a href="https://github.com/huggingface/tgi-gaudi">TGI Gaudi</a></td>
			<td>Gaudi2</td>
			<td>LLM on Gaudi2</td>
		</tr>
		<tr>
			<td><a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
			<td>Xeon</td>
			<td>LLM on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="2"><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">Intel/neural-chat-7b-v3-3</a></td>
			<td rowspan="2"><a href="https://github.com/ray-project/ray">Ray Serve</a></td>
			<td>Gaudi2</td>
			<td>LLM on Gaudi2</td>
		</tr>
		<tr>
			<td>Xeon</td>
			<td>LLM on Xeon CPU</td>
		</tr>
		<tr>
			<td rowspan="2"><a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">Intel/neural-chat-7b-v3-3</a></td>
			<td rowspan="2"><a href="https://github.com/vllm-project/vllm/">vLLM</a></td>
			<td>Gaudi2</td>
			<td>LLM on Gaudi2</td>
		</tr>
		<tr>
			<td>Xeon</td>
			<td>LLM on Xeon CPU</td>
		</tr>
	</tbody>
</table>

A `Microservices` can be created by using the decorator `register_microservice`. Taking the `embedding microservice` as an example:

```python
from langchain_community.embeddings import HuggingFaceHubEmbeddings

from comps import register_microservice, EmbedDoc, ServiceType, TextDoc


@register_microservice(
    name="opea_service@embedding_tgi_gaudi",
    service_type=ServiceType.EMBEDDING,
    endpoint="/v1/embeddings",
    host="0.0.0.0",
    port=6000,
    input_datatype=TextDoc,
    output_datatype=EmbedDoc,
)
def embedding(input: TextDoc) -> EmbedDoc:
    embed_vector = embeddings.embed_query(input.text)
    res = EmbedDoc(text=input.text, embedding=embed_vector)
    return res
```

## MegaService

A `Megaservice` is a higher-level architectural construct composed of one or more `Microservices`, providing the capability to assemble end-to-end applications. Unlike individual `Microservices`, which focus on specific tasks or functions, a `Megaservice` orchestrates multiple `Microservices` to deliver a comprehensive solution.

`Megaservices` encapsulate complex business logic and workflow orchestration, coordinating the interactions between various `Microservices` to fulfill specific application requirements. This approach enables the creation of modular yet integrated applications, where each `Microservice` contributes to the overall functionality of the `Megaservice`.

Here is a simple example of building `Megaservice`:

```python
from comps import MicroService, ServiceOrchestrator

EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)


class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(embedding).add(llm)
        self.megaservice.flow_to(embedding, llm)
```

## Gateway

The `Gateway` serves as the interface for users to access the `Megaservice`, providing customized access based on user requirements. It acts as the entry point for incoming requests, routing them to the appropriate `Microservices` within the `Megaservice` architecture.

`Gateways` support API definition, API versioning, rate limiting, and request transformation, allowing for fine-grained control over how users interact with the underlying `Microservices`. By abstracting the complexity of the underlying infrastructure, `Gateways` provide a seamless and user-friendly experience for interacting with the `Megaservice`.

For example, the `Gateway` for `ChatQnA` can be built like this:

```python
from comps import ChatQnAGateway

self.gateway = ChatQnAGateway(megaservice=self.megaservice, host="0.0.0.0", port=self.port)
```

## Additional Content

- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Contribution](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
