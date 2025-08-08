# Agents for Question and Answering Application

## Table of contents

1. [Build Service Docker Image](#build-service-docker-image)
2. [Build UI Docker Image](#build-ui-docker-image)
3. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
4. [Monitor and Tracing](#monitor-and-tracing)

# Build Service Docker Image

To construct the Megaservice of AgentQnA, the [GenAIExamples](https://github.com/opea-project/GenAIExamples.git) repository is utilized. Build service Docker image via command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AgentQnA/docker_image_build
git clone https://github.com/opea-project/GenAIComps.git
# build for Intel Gaudi
service_list="vllm-gaudi agent agent-ui"
# build for AMD ROCm
service_list="vllm-rocm agent agent-ui"
docker compose -f build.yaml build ${service_list} --no-cache
```

You also need to build DocIndexRetriever docker images:

```bash
cd GenAIExamples/DocIndexRetriever/docker_image_build/
git clone https://github.com/opea-project/GenAIComps.git
service_list="doc-index-retriever dataprep embedding retriever reranking"
docker compose -f build.yaml build ${service_list} --no-cache
```

## Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/AgentQnA/ui
docker build -t opea/AgentQnA-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

## Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if the developer have an access token. In the absence of a HuggingFace access token, the developer can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

## Monitor and Tracing

Follow [OpenTelemetry OPEA Guide](https://opea-project.github.io/latest/tutorial/OpenTelemetry/OpenTelemetry_OPEA_Guide.html) to understand how to use OpenTelemetry tracing and metrics in OPEA.  
For AgentQnA specific tracing and metrics monitoring, follow [OpenTelemetry on AgentQnA](https://opea-project.github.io/latest/tutorial/OpenTelemetry/deploy/AgentQnA.html) section.
