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

| MicroService                                  | Framework                                                                      | Model                                                                                                   | Serving                                                         | HW     | Description                           |
| --------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ------ | ------------------------------------- |
| [Embedding](./comps/embeddings/README.md)     | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5)                                   | [TEI-Gaudi](https://github.com/huggingface/tei-gaudi)           | Gaudi2 | Embedding on Gaudi2                   |
| [Embedding](./comps/embeddings/README.md)     | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5)                                   | [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon   | Embedding on Xeon CPU                 |
| [Retriever](./comps/retrievers/README.md)     | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5)                                   | [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon   | Retriever on Xeon CPU                 |
| [Reranking](./comps/reranks/tei/README.md)    | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BAAI/bge-reranker-base](https://huggingface.co/BAAI/bge-reranker-base)                                 | [TEI-Gaudi](https://github.com/huggingface/tei-gaudi)           | Gaudi2 | Reranking on Gaudi2                   |
| [Reranking](./comps/reranks/tei/README.md)    | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BBAAI/bge-reranker-base](https://huggingface.co/BAAI/bge-reranker-base)                                | [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon   | Reranking on Xeon CPU                 |
| [ASR](./comps/asr/whisper/README.md)          | NA                                                                             | [openai/whisper-small](https://huggingface.co/openai/whisper-small)                                     | NA                                                              | Gaudi2 | Audio-Speech-Recognition on Gaudi2    |
| [ASR](./comps/asr/whisper/README.md)          | NA                                                                             | [openai/whisper-small](https://huggingface.co/openai/whisper-small)                                     | NA                                                              | Xeon   | Audio-Speech-RecognitionS on Xeon CPU |
| [TTS](./comps/tts/speecht5/README.md)         | NA                                                                             | [microsoft/speecht5_tts](https://huggingface.co/microsoft/speecht5_tts)                                 | NA                                                              | Gaudi2 | Text-To-Speech on Gaudi2              |
| [TTS](./comps/tts/speecht5/README.md)         | NA                                                                             | [microsoft/speecht5_tts](https://huggingface.co/microsoft/speecht5_tts)                                 | NA                                                              | Xeon   | Text-To-Speech on Xeon CPU            |
| [Dataprep](./comps/dataprep/README.md)        | [Qdrant](https://qdrant.tech/)                                                 | [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | NA                                                              | Gaudi2 | Dataprep on Gaudi2                    |
| [Dataprep](./comps/dataprep/README.md)        | [Qdrant](https://qdrant.tech/)                                                 | [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | NA                                                              | Xeon   | Dataprep on Xeon CPU                  |
| [Dataprep](./comps/dataprep/README.md)        | [Redis](https://redis.io/)                                                     | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5)                                   | NA                                                              | Gaudi2 | Dataprep on Gaudi2                    |
| [Dataprep](./comps/dataprep/README.md)        | [Redis](https://redis.io/)                                                     | [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5)                                   | NA                                                              | Xeon   | Dataprep on Xeon CPU                  |
| [LLM](./comps/llms/text-generation/README.md) | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3)                           | [TGI Gaudi](https://github.com/huggingface/tgi-gaudi)           | Gaudi2 | LLM on Gaudi2                         |
| [LLM](./comps/llms/text-generation/README.md) | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3)                           | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon   | LLM on Xeon CPU                       |
| [LLM](./comps/llms/text-generation/README.md) | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3)                           | [Ray Serve](https://github.com/ray-project/ray)                 | Gaudi2 | LLM on Gaudi2                         |
| [LLM](./comps/llms/text-generation/README.md) | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3)                           | [Ray Serve](https://github.com/ray-project/ray)                 | Xeon   | LLM on Xeon CPU                       |
| [LLM](./comps/llms/text-generation/README.md) | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3)                           | [vLLM](https://github.com/vllm-project/vllm/)                   | Gaudi2 | LLM on Gaudi2                         |
| [LLM](./comps/llms/text-generation/README.md) | [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3)                           | [vLLM](https://github.com/vllm-project/vllm/)                   | Xeon   | LLM on Xeon CPU                       |

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

## Contributing to OPEA

Welcome to the OPEA open-source community! We are thrilled to have you here and excited about the potential contributions you can bring to the OPEA platform. Whether you are fixing bugs, adding new GenAI components, improving documentation, or sharing your unique use cases, your contributions are invaluable.

Together, we can make OPEA the go-to platform for enterprise AI solutions. Let's work together to push the boundaries of what's possible and create a future where AI is accessible, efficient, and impactful for everyone.

Please check the [Contributing guidelines](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md) for a detailed guide on how to contribute a GenAI example and all the ways you can contribute!

Thank you for being a part of this journey. We can't wait to see what we can achieve together!

## Additional Content

- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
