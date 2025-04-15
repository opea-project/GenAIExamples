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

| Framework                                                                      | LLM                                                                                     | Serving                                                         | HW          | Description |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ----------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [Qwen/Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Copilot     |

### CodeTrans

[CodeTrans](./CodeTrans/README.md) is an example of chatbot for converting code written in one programming language to another programming language while maintaining the same functionality.

| Framework                                                                      | LLM                                                                                             | Serving                                                         | HW          | Description      |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------- | ---------------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [mistralai/Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) | [TGI](https://github.com/huggingface/text-generation-inference) | Xeon/Gaudi2 | Code Translation |

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

| LVM                                                                                           | HW          | Description |
| --------------------------------------------------------------------------------------------- | ----------- | ----------- |
| [llava-hf/llava-v1.6-mistral-7b-hf](https://huggingface.co/llava-hf/llava-v1.6-mistral-7b-hf) | Xeon/Gaudi2 | Chatbot     |

### VideoQnA

[VideoQnA](./VideoQnA/README.md) is an example of chatbot for question and answering based on the videos. It retrieves video based on provided user prompt. It uses only the video embeddings to perform vector similarity search in Intel's VDMS vector database and performs all operations on Intel Xeon CPU. The pipeline supports long form videos and time-based search.

By default, the embedding and LVM models are set to a default value as listed below:

| Service   | Model                                                                               | HW   | Description              |
| --------- | ----------------------------------------------------------------------------------- | ---- | ------------------------ |
| Embedding | [openai/clip-vit-base-patch32](https://huggingface.co/openai/clip-vit-base-patch32) | Xeon | Video embeddings service |
| LVM       | [DAMO-NLP-SG/Video-LLaMA](https://huggingface.co/DAMO-NLP-SG/VideoLLaMA2-7B)        | Xeon | LVM service              |

### RerankFinetuning

[Rerank model finetuning](./RerankFinetuning/README.md) example is for training rerank model on a dataset for improving its capability on specific field.

By default, the base model is set to a default value as listed below:

| Service           | Base Model                                                                | HW          | Description                     |
| ----------------- | ------------------------------------------------------------------------- | ----------- | ------------------------------- |
| Rerank Finetuning | [BAAI/bge-reranker-large](https://huggingface.co/BAAI/bge-reranker-large) | Xeon/Gaudi2 | Rerank model finetuning service |

### InstructionTuning

The [Instruction Tuning](./InstructionTuning/README.md) example is designed to further train large language models (LLMs) on a dataset consisting of (instruction, output) pairs using supervised learning. This process bridges the gap between the LLM's original objective of next-word prediction and the user’s objective of having the model follow human instructions accurately. By leveraging Instruction Tuning, this example enhances the LLM's ability to better understand and execute specific tasks, improving the model's alignment with user instructions and its overall performance.

By default, the base model is set to a default value as listed below:

| Service           | Base Model                                                                            | HW          | Description                          |
| ----------------- | ------------------------------------------------------------------------------------- | ----------- | ------------------------------------ |
| InstructionTuning | [meta-llama/Llama-2-7b-chat-hf](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf) | Xeon/Gaudi2 | LLM model Instruction Tuning service |

### DocIndexRetriever

The [DocRetriever](./DocIndexRetriever/README.md) example demonstrates how to match user queries with free-text records using various retrieval methods. It plays a key role in Retrieval-Augmented Generation (RAG) systems by dynamically fetching relevant information from external sources, ensuring responses are factual and up-to-date. Powered by vector databases, DocRetriever enables efficient, semantic retrieval by storing data as vectors and quickly identifying the most relevant documents based on similarity.

| Framework                                                                      | Embedding                                           | Vector Database            | Serving                                                         | HW          | Description                |
| ------------------------------------------------------------------------------ | --------------------------------------------------- | -------------------------- | --------------------------------------------------------------- | ----------- | -------------------------- |
| [LangChain](https://www.langchain.com)/[LlamaIndex](https://www.llamaindex.ai) | [BGE-Base](https://huggingface.co/BAAI/bge-base-en) | [Redis](https://redis.io/) | [TEI](https://github.com/huggingface/text-embeddings-inference) | Xeon/Gaudi2 | Document Retrieval service |

### AgentQnA

The [AgentQnA](./AgentQnA/README.md) example demonstrates a hierarchical, multi-agent system designed for question-answering tasks. A supervisor agent interacts directly with the user, delegating tasks to a worker agent and utilizing various tools to gather information and generate answers. The worker agent primarily uses a retrieval tool to respond to the supervisor's queries. Additionally, the supervisor can access other tools, such as APIs to query knowledge graphs, SQL databases, or external knowledge bases, to enhance the accuracy and relevance of its responses.

Worker agent uses open-source websearch tool (duckduckgo), agents use OpenAI GPT-4o-mini as llm backend.

> **_NOTE:_** This example is in active development. The code structure of these use cases are subject to change.

### AudioQnA

The [AudioQnA](./AudioQnA/README.md) example demonstrates the integration of Generative AI (GenAI) models for performing question-answering (QnA) on audio files, with the added functionality of Text-to-Speech (TTS) for generating spoken responses. The example showcases how to convert audio input to text using Automatic Speech Recognition (ASR), generate answers to user queries using a language model, and then convert those answers back to speech using Text-to-Speech (TTS).

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

### MultimodalQnA

[MultimodalQnA](./MultimodalQnA/README.md) addresses your questions by dynamically fetching the most pertinent multimodal information (frames, transcripts, and/or captions) from your collection of videos, images, or audio files. MultimodalQnA utilizes BridgeTower model, a multimodal encoding transformer model which merges visual and textual data into a unified semantic space. During the ingestion phase, the BridgeTower model embeds both visual cues and auditory facts as texts, and those embeddings are then stored in a vector database. When it comes to answering a question, the MultimodalQnA will fetch its most relevant multimodal content from the vector store and feed it into a downstream Large Vision-Language Model (LVM) as input context to generate a response for the user.

| Service   | Model                                                                                                             | HW         | Description                   |
| --------- | ----------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------- |
| Embedding | [BridgeTower/bridgetower-large-itm-mlm-itc](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-itc)     | Xeon/Gaudi | Multimodal embeddings service |
| Embedding | [BridgeTower/bridgetower-large-itm-mlm-gaudi](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) | Gaudi      | Multimodal embeddings service |
| LVM       | [llava-hf/llava-1.5-7b-hf](https://huggingface.co/llava-hf/llava-1.5-7b-hf)                                       | Xeon       | LVM service                   |
| LVM       | [llava-hf/llava-1.5-13b-hf](https://huggingface.co/llava-hf/llava-1.5-13b-hf)                                     | Xeon       | LVM service                   |
| LVM       | [llava-hf/llava-v1.6-vicuna-13b-hf](https://huggingface.co/llava-hf/llava-v1.6-vicuna-13b-hf)                     | Gaudi      | LVM service                   |

### ProductivitySuite

[Productivity Suite](./ProductivitySuite/README.md) streamlines your workflow to boost productivity. It leverages the power of OPEA microservices to deliver a comprehensive suite of features tailored to meet the diverse needs of modern enterprises.

### DBQnA

[DBQnA](./DBQnA/README.md) converts your natural language query into an SQL query, automatically executes the generated query on the database and delivers real-time query results.
| Framework | LLM | Database | HW | Description |
|----------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|------|----------------------------|
| [LangChain](https://www.langchain.com) | [mistralai/Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) | [PostgresDB](https://www.postgresql.org/) | Xeon | Natural language SQL agent |

### Text2Image

[Text2Image](./Text2Image/README.md) generates image based on your provided text.
| Framework | LDM | HW | Description |
|----------------------------------------|--------------------------------------------------------------------------------------------------------|-------------|-------------|
| [LangChain](https://www.langchain.com) | [stabilityai/stable-diffusion](https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers) | Xeon/Gaudi2 | Text2Image |

### AvatarChatbot

[AvatarChatbot](./AvatarChatbot/README.md) example is a chatbot with a visual character that provides users dynamic, engaging interactions, by leveraging multiple generative AI components including LLM, ASR (Audio-Speech-Recognition), and TTS (Text-To-Speech).
| LLM | ASR | TTS | Animation | HW | Description |
|-------------------------------------------------------------------------------|---------------------------------------------------------------------|---------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|-------------|----------------------------|
| [Intel/neural-chat-7b-v3-3](https://huggingface.co/Intel/neural-chat-7b-v3-3) | [openai/whisper-small](https://huggingface.co/openai/whisper-small) | [microsoft/SpeechT5](https://huggingface.co/microsoft/speecht5_tts) | [Rudrabha/Wav2Lip](https://github.com/Rudrabha/Wav2Lip) <br> [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN) | Xeon/Gaudi2 | Interactive chatbot Avatar |
