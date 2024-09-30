# Supported Examples

This document introduces the supported examples of GenAIExamples. The supported Vector Database, LLM models, serving frameworks and hardwares are listed as below.

## ChatQnA

[ChatQnA](./ChatQnA/README.md) is an example of chatbot for question and answering through retrieval augmented generation (RAG).

<table>
    <tr>
        <th>Framework</th>
        <th>LLM</th>
        <th>Embedding</th>
        <th>Vector Database</th>
        <th>Serving</th>
        <th>HW</th>
        <th>Description</th>
    </tr>
    <tr>
        <td rowspan="6"><a href="https://www.langchain.com">LangChain</a>/<a href="https://www.llamaindex.ai/">LlamaIndex</a></td>
        <td> <a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
        <td> <a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
        <td> <a href="https://redis.io/">Redis</a></td>
        <td> <a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
        <td> Xeon/Gaudi2/GPU</td>
        <td> Chatbot</td>
    </tr>
    <tr>
        <td> <a href="https://huggingface.co/Intel/neural-chat-7b-v3-3">NeuralChat-7B</a></td>
        <td> <a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
        <td> <a href="https://www.trychroma.com/">Chroma</a></td>
        <td> <a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
        <td> Xeon/Gaudi2</td>
        <td> Chatbot</td>
    </tr>
    <tr>
        <td> <a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
        <td> <a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
        <td> <a href="https://redis.io/">Redis</a></td>
        <td> <a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
        <td> Xeon/Gaudi2</td>
        <td> Chatbot</td>
    </tr>
    <tr>
        <td> <a href="https://huggingface.co/mistralai/Mistral-7B-v0.1">Mistral-7B</a></td>
        <td> <a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
        <td> <a href="https://qdrant.tech/">Qdrant</a></td>
        <td> <a href="https://github.com/huggingface/text-generation-inference">TGI</a> <a href="https://github.com/huggingface/text-embeddings-inference">TEI</a></td>
        <td> Xeon/Gaudi2</td>
        <td> Chatbot</td>
    </tr>
    <tr>
        <td> <a href="https://huggingface.co/Qwen/Qwen2-7B">Qwen2-7B</a></td>
        <td> <a href="https://huggingface.co/BAAI/bge-base-en">BGE-Base</a></td>
        <td> <a href="https://redis.io/">Redis</a></td>
        <td> <a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
        <td> Xeon/Gaudi2</td>
        <td> Chatbot</td>
    </tr>
</table>

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

| LVM                                                                                           | HW     | Description |
| --------------------------------------------------------------------------------------------- | ------ | ----------- |
| [llava-hf/llava-v1.6-mistral-7b-hf](https://huggingface.co/llava-hf/llava-v1.6-mistral-7b-hf) | Gaudi2 | Chatbot     |

### VideoQnA

[VideoQnA](./VideoQnA/README.md) is an example of chatbot for question and answering based on the videos. It retrieves video based on provided user prompt. It uses only the video embeddings to perform vector similarity search in Intel's VDMS vector database and performs all operations on Intel Xeon CPU. The pipeline supports long form videos and time-based search.

By default, the embedding and LVM models are set to a default value as listed below:

| Service   | Model                                                                               | HW   | Description              |
| --------- | ----------------------------------------------------------------------------------- | ---- | ------------------------ |
| Embedding | [openai/clip-vit-base-patch32](https://huggingface.co/openai/clip-vit-base-patch32) | Xeon | Video embeddings service |
| LVM       | [DAMO-NLP-SG/Video-LLaMA](https://huggingface.co/DAMO-NLP-SG/VideoLLaMA2-7B)        | Xeon | LVM service              |

### RerankFinetuning

Rerank model finetuning example is for training rerank model on a dataset for improving its capability on specific field.

By default, the base model is set to a default value as listed below:

| Service           | Base Model                                                                | HW   | Description                     |
| ----------------- | ------------------------------------------------------------------------- | ---- | ------------------------------- |
| Rerank Finetuning | [BAAI/bge-reranker-large](https://huggingface.co/BAAI/bge-reranker-large) | Xeon | Rerank model finetuning service |

### InstructionTuning

The Instruction Tuning example is designed to further train large language models (LLMs) on a dataset consisting of (instruction, output) pairs using supervised learning. This process bridges the gap between the LLM's original objective of next-word prediction and the user’s objective of having the model follow human instructions accurately. By leveraging Instruction Tuning, this example enhances the LLM's ability to better understand and execute specific tasks, improving the model's alignment with user instructions and its overall performance.

By default, the base model is set to a default value as listed below:

| Service           | Base Model                                                                            | HW         | Description                          |
| ----------------- | ------------------------------------------------------------------------------------- | ---------- | ------------------------------------ |
| InstructionTuning | [meta-llama/Llama-2-7b-chat-hf](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf) | Xeon/Gaudi | LLM model Instruction Tuning service |

### DocIndexRetriever

The DocRetriever example demonstrates how to match user queries with free-text records using various retrieval methods. It plays a key role in Retrieval-Augmented Generation (RAG) systems by dynamically fetching relevant information from external sources, ensuring responses are factual and up-to-date. Powered by vector databases, DocRetriever enables efficient, semantic retrieval by storing data as vectors and quickly identifying the most relevant documents based on similarity.

| Framework                                                                      | Embedding                                           | Vector Database            | Serving                                                         | HW          | Description                |
| ------------------------------------------------------------------------------ | --------------------------------------------------- | -------------------------- | --------------------------------------------------------------- | ----------- | -------------------------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Redis](https://redis.io/) | [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon/Gaudi2 | Document Retrieval service |

### AgentQnA

The AgentQnA example demonstrates a hierarchical, multi-agent system designed for question-answering tasks. A supervisor agent interacts directly with the user, delegating tasks to a worker agent and utilizing various tools to gather information and generate answers. The worker agent primarily uses a retrieval tool to respond to the supervisor's queries. Additionally, the supervisor can access other tools, such as APIs to query knowledge graphs, SQL databases, or external knowledge bases, to enhance the accuracy and relevance of its responses.

Worker agent uses open-source websearch tool (duckduckgo), agents use OpenAI GPT-4o-mini as llm backend.

> **_NOTE:_** This example is in active development. The code structure of these use cases are subject to change.

### AudioQnA

The AudioQnA example demonstrates the integration of Generative AI (GenAI) models for performing question-answering (QnA) on audio files, with the added functionality of Text-to-Speech (TTS) for generating spoken responses. The example showcases how to convert audio input to text using Automatic Speech Recognition (ASR), generate answers to user queries using a language model, and then convert those answers back to speech using Text-to-Speech (TTS).

<table>
    <tr>
        <th>ASR</th>
        <th>TTS</th>
        <th>LLM</th>
        <th>HW</th>
        <th>Description</th>
    </tr>
    <tr>
        <td> <a href="https://huggingface.co/openai/whisper-small">openai/whisper-small</a></td>
        <td> <a href="https://huggingface.co/microsoft/speecht5_tts">microsoft/SpeechT5</a></td>
        <td> <a href="https://github.com/huggingface/text-generation-inference">TGI</a></td>
        <td> Xeon/Gaudi2</td>
        <td> Talkingbot service</td>
    </tr>
</table>

### FaqGen

FAQ Generation Application leverages the power of large language models (LLMs) to revolutionize the way you interact with and comprehend complex textual data. By harnessing cutting-edge natural language processing techniques, our application can automatically generate comprehensive and natural-sounding frequently asked questions (FAQs) from your documents, legal texts, customer queries, and other sources. In this example use case, we utilize LangChain to implement FAQ Generation and facilitate LLM inference using Text Generation Inference on Intel Xeon and Gaudi2 processors.
| Framework | LLM | Serving | HW | Description |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ----------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Meta-Llama-3-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Chatbot |

### MultimodalQnA

[MultimodalQnA](./MultimodalQnA/README.md) addresses your questions by dynamically fetching the most pertinent multimodal information (frames, transcripts, and/or captions) from your collection of videos.

### ProductivitySuite

[Productivity Suite](./ProductivitySuite/README.md) streamlines your workflow to boost productivity. It leverages the power of OPEA microservices to deliver a comprehensive suite of features tailored to meet the diverse needs of modern enterprises.
