# AudioQnA Docker Image Build

## Table of Contents

1. [Build MegaService Docker Image](#build-megaservice-docker-image)
2. [Build UI Docker Image](#build-ui-docker-image)
3. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
4. [Troubleshooting](#troubleshooting)

## Build MegaService Docker Image

To construct the Megaservice of AudioQnA, the [GenAIExamples](https://github.com/opea-project/GenAIExamples.git) repository is utilized. Build Megaservice Docker image using command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA
docker build --no-cache -t opea/audioqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

## Build UI Docker Image

Build frontend Docker image using below command:

```bash
cd GenAIExamples/AudioQnA/ui
docker build -t opea/audioqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

## Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if the developer has an access token. In the absence of a HuggingFace access token, the developer can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/AudioQnA/docker_compose/intel/cpu/xeon/README.md#validate-microservices) first. A simple example:

   ```bash
   curl http://${host_ip}:7055/v1/audio/speech -XPOST -d '{"input": "Who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:7777, the port may be allocated by other users, you can modify the `compose.yaml`.
3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.
