# Build MegaService of CodeGen on Gaudi

This document outlines the deployment process for a CodeGen application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi2 server. The steps include Docker images creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to the Docker Hub soon, further simplifying the deployment process for this service.

The default pipeline deploys with vLLM as the LLM serving component. It also provides options of using TGI backend for LLM microservice.

## 🚀 Start MicroServices and MegaService

The CodeGen megaservice manages a several microservices including 'Embedding MicroService', 'Retrieval MicroService' and 'LLM MicroService' within a Directed Acyclic Graph (DAG). In the diagram below, the LLM microservice is a language model microservice that generates code snippets based on the user's input query. The TGI service serves as a text generation interface, providing a RESTful API for the LLM microservice. Data Preparation allows users to save/update documents or online resources to the vector database. Users can upload files or provide URLs, and manage their saved resources. The CodeGen Gateway acts as the entry point for the CodeGen application, invoking the Megaservice to generate code snippets in response to the user's input query.

The mega flow of the CodeGen application, from user's input query to the application's output response, is as follows:

```mermaid
---
config:
  flowchart:
    nodeSpacing: 400
    rankSpacing: 100
    curve: linear
  themeVariables:
    fontSize: 25px
---
flowchart LR
    %% Colors %%
    classDef blue fill:#ADD8E6,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orange fill:#FBAA60,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orchid fill:#C26DBC,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef invisible fill:transparent,stroke:transparent;
    style CodeGen-MegaService stroke:#000000
    %% Subgraphs %%
    subgraph CodeGen-MegaService["CodeGen-MegaService"]
        direction LR
        EM([Embedding<br>MicroService]):::blue
        RET([Retrieval<br>MicroService]):::blue
        RER([Agents]):::blue
        LLM([LLM<br>MicroService]):::blue
    end
    subgraph User Interface
        direction LR
        a([Submit Query Tab]):::orchid
        UI([UI server]):::orchid
        Ingest([Manage Resources]):::orchid
    end

    CLIP_EM{{Embedding<br>service}}
    VDB{{Vector DB}}
    V_RET{{Retriever<br>service}}
    Ingest{{Ingest data}}
    DP([Data Preparation]):::blue
    LLM_gen{{TGI Service}}
    GW([CodeGen GateWay]):::orange

    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] --> UI
    UI --> DP
    DP <-.-> CLIP_EM

    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI --> GW
    GW <==> CodeGen-MegaService
    EM ==> RET
    RET ==> RER
    RER ==> LLM


    %% Embedding service flow
    direction LR
    EM <-.-> CLIP_EM
    RET <-.-> V_RET
    LLM <-.-> LLM_gen

    direction TB
    %% Vector DB interaction
    V_RET <-.->VDB
    DP <-.->VDB
```

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

1. set the host_ip and huggingface token

> [!NOTE]
> Please replace the `your_ip_address` with you external IP address, do not use `localhost`.

```bash
export host_ip=${your_ip_address}
export HUGGINGFACEHUB_API_TOKEN=you_huggingface_token
```

2. Set Network Proxy

**If you access public network through proxy, set the network proxy, otherwise, skip this step**

```bash
export no_proxy=${no_proxy},${host_ip}
export http_proxy=${your_http_proxy}
export https_proxy=${your_https_proxy}
```

## 🚀 Build Docker Images

First of all, you need to build the Docker images locally. This step can be ignored after the Docker images published to the Docker Hub.

### 1. Build the LLM Docker Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/llm-textgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

### 2. Build the Retriever Image

```bash
docker build -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

### 3. Build the Dataprep Image

```bash
docker build -t opea/dataprep:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
```

### 4. Build the MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `codegen.py` Python script. Build the MegaService Docker image via the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen
docker build -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 5. Build the UI Gradio Image (Recommended)

Build the frontend Gradio image via the command below:

```bash
cd GenAIExamples/CodeGen/ui
docker build -t opea/codegen-gradio-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile.gradio .
```

### 5a. Build CodeGen React UI Docker Image (Optional)

Build react frontend Docker image via below command:

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

```bash
cd GenAIExamples/CodeGen/ui
docker build --no-cache -t opea/codegen-react-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile.react .
```

### 5b. Build the UI Docker Image

Construct the frontend Docker image via the command below:

```bash
cd GenAIExamples/CodeGen/ui
docker build -t opea/codegen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker images:

- `opea/llm-textgen:latest`
- `opea/retriever:latest`
- `opea/dataprep:latest`
- `opea/codegen:latest`
- `opea/codegen-gradio-ui:latest` (Recommended)
- `opea/codegen-ui:latest` (Optional)
- `opea/codegen-react-ui:latest` (Optional)

### Start the Docker Containers for All Services

#### Deploy CodeGen on Gaudi

Find the corresponding [compose.yaml](./docker_compose/intel/hpu/gaudi/compose.yaml). User could start CodeGen based on TGI or vLLM service:

```bash
cd GenAIExamples/CodeGen/docker_compose/intel/hpu/gaudi
```

TGI service:

```bash
docker compose --profile codegen-gaudi-tgi up -d
```

vLLM service:

```bash
docker compose --profile codegen-gaudi-vllm up -d
```

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) to build docker images from source.

#### Deploy CodeGen on Xeon

Find the corresponding [compose.yaml](./docker_compose/intel/cpu/xeon/compose.yaml). User could start CodeGen based on TGI or vLLM service:

```bash
cd GenAIExamples/CodeGen/docker_compose/intel/cpu/xeon
```

TGI service:

```bash
docker compose --profile codegen-xeon-tgi up -d
```

vLLM service:

```bash
docker compose --profile codegen-xeon-vllm up -d
```

### Validate the MicroServices and MegaService

1. LLM Service (for TGI, vLLM)

   ```bash
   curl http://${host_ip}:8028/v1/chat/completions \
       -X POST \
       -H 'Content-Type: application/json' \
       -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."}], "max_tokens":32}'

   ```

2. LLM Microservices

   ```bash
   curl http://${host_ip}:9000/v1/chat/completions\
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{"query":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","max_tokens":256,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"stream":true}'
   ```

3. Dataprep Microservice

   Make sure to replace the file name placeholders with your correct file name

   ```bash
   curl http://${host_ip}:6007/v1/dataprep/ingest \
   -X POST \
   -H "Content-Type: multipart/form-data" \
   -F "files=@./file1.pdf" \
   -F "files=@./file2.txt" \
   -F "index_name=my_API_document"
   ```

4. MegaService

   ```bash
   curl http://${host_ip}:7778/v1/codegen \
     -H "Content-Type: application/json" \
     -d '{"messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."}'
   ```

   CodeGen service with RAG and Agents activated based on an index.

   ```bash
   curl http://${host_ip}$:7778/v1/codegen \
     -H "Content-Type: application/json" \
     -d '{"agents_flag": "True", "index_name": "my_API_document", "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."}'
   ```

## 🚀 Launch the Gradio Based UI (Recommended)

To access the Gradio frontend URL, follow the steps in [this README](../../../../ui/gradio/README.md)

Code Generation Tab
![project-screenshot](../../../../assets/img/codegen_gradio_ui_main.png)

Resource Management Tab
![project-screenshot](../../../../assets/img/codegen_gradio_ui_main.png)

Uploading a Knowledge Index

![project-screenshot](../../../../assets/img/codegen_gradio_ui_dataprep.png)

Here is an example of running a query in the Gradio UI using an Index:

![project-screenshot](../../../../assets/img/codegen_gradio_ui_query.png)

## 🚀 Launch the Svelte Based UI (Optional)

To access the frontend, open the following URL in your browser: `http://{host_ip}:5173`. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  codegen-gaudi-ui-server:
    image: opea/codegen-ui:latest
    ...
    ports:
      - "80:5173"
```

![project-screenshot](../../../../assets/img/codeGen_ui_init.jpg)

## 🚀 Launch the React Based UI (Optional)

To access the React-based frontend, modify the UI service in the `compose.yaml` file. Replace `codegen-gaudi-ui-server` service with the `codegen-gaudi-react-ui-server` service as per the config below:

```yaml
codegen-gaudi-react-ui-server:
  image: ${REGISTRY:-opea}/codegen-react-ui:${TAG:-latest}
  container_name: codegen-gaudi-react-ui-server
  environment:
    - no_proxy=${no_proxy}
    - https_proxy=${https_proxy}
    - http_proxy=${http_proxy}
    - APP_CODE_GEN_URL=${BACKEND_SERVICE_ENDPOINT}
  depends_on:
    - codegen-gaudi-backend-server
  ports:
    - "5174:80"
  ipc: host
  restart: always
```

![project-screenshot](../../../../assets/img/codegen_react.png)

## Install Copilot VSCode extension from Plugin Marketplace as the frontend

In addition to the Svelte UI, users can also install the Copilot VSCode extension from the Plugin Marketplace as the frontend.

Install `Neural Copilot` in VSCode as below.

![Install-screenshot](../../../../assets/img/codegen_copilot.png)

### How to Use

#### Service URL Setting

Please adjust the service URL in the extension settings based on the endpoint of the CodeGen backend service.

![Setting-screenshot](../../../../assets/img/codegen_settings.png)
![Setting-screenshot](../../../../assets/img/codegen_endpoint.png)

#### Customize

The Copilot enables users to input their corresponding sensitive information and tokens in the user settings according to their own needs. This customization enhances the accuracy and output content to better meet individual requirements.

![Customize](../../../../assets/img/codegen_customize.png)

#### Code Suggestion

To trigger inline completion, you'll need to type `# {your keyword} (start with your programming language's comment keyword, like // in C++ and # in python)`. Make sure the `Inline Suggest` is enabled from the VS Code Settings.
For example:

![code suggestion](../../../../assets/img/codegen_suggestion.png)

To provide programmers with a smooth experience, the Copilot supports multiple ways to trigger inline code suggestions. If you are interested in the details, they are summarized as follows:

- Generate code from single-line comments: The simplest way introduced before.
- Generate code from consecutive single-line comments:

![codegen from single-line comments](../../../../assets/img/codegen_single_line.png)

- Generate code from multi-line comments, which will not be triggered until there is at least one `space` outside the multi-line comment):

![codegen from multi-line comments](../../../../assets/img/codegen_multi_line.png)

- Automatically complete multi-line comments:

![auto complete](../../../../assets/img/codegen_auto_complete.jpg)

### Chat with AI assistant

You can start a conversation with the AI programming assistant by clicking on the robot icon in the plugin bar on the left:

![icon](../../../../assets/img/codegen_icon.png)

Then you can see the conversation window on the left, where you can chat with the AI assistant:

![dialog](../../../../assets/img/codegen_dialog.png)

There are 4 areas worth noting as shown in the screenshot above:

1. Enter and submit your question
2. Your previous questions
3. Answers from AI assistant (Code will be highlighted properly according to the programming language it is written in, also support stream output)
4. Copy or replace code with one click (Note that you need to select the code in the editor first and then click "replace", otherwise the code will be inserted)

You can also select the code in the editor and ask the AI assistant questions about the code directly.
For example:

- Select code

![select code](../../../../assets/img/codegen_select_code.png)

- Ask question and get answer

![qna](../../../../assets/img/codegen_qna.png)
