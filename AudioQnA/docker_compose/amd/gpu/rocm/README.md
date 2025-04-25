# Deploying AudioQnA on AMD ROCm GPU

This document outlines the single node deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on server with AMD ROCm processing accelerators. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.

Note: The default LLM is `Intel/neural-chat-7b-v3-3`. Before deploying the application, please make sure either you've requested and been granted the access to it on [Huggingface](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) or you've downloaded the model locally from [ModelScope](https://www.modelscope.cn/models).

## Table of Contents

1. [AudioQnA Quick Start Deployment](#audioqna-quick-start-deployment)
2. [AudioQnA Docker Compose Files](#audioqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## AudioQnA Quick Start Deployment

This section describes how to quickly deploy and test the AudioQnA service manually on an AMD ROCm platform. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the AudioQnA AMD ROCm platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA
```

Then checkout a released version, such as v1.3:

```bash
git checkout v1.3
```

### Configure the Deployment Environment

#### Docker Compose GPU Configuration

Consult the section on [AudioQnA Service configuration](#audioqna-configuration) for information on how service specific configuration parameters affect deployments.

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose files (`compose.yaml`, `compose_vllm.yaml`) for the LLM serving container:

```yaml
# Example for vLLM service in compose_vllm.yaml
# Note: Modern docker compose might use deploy.resources syntax instead.
# Check your docker version and compose file.
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/:/dev/dri/
# - /dev/dri/render128:/dev/dri/render128
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

#### Environment Variables (`set_env*.sh`)

These scripts (`set_env_vllm.sh` for vLLM, `set_env.sh` for TGI) configure crucial parameters passed to the containers.

To set up environment variables for deploying AudioQnA services, set up some parameters specific to the deployment environment and source the `set_env.sh` script in this directory:

For TGI inference usage:

```bash
export host_ip="External_Public_IP"           # ip address of the node
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip,whisper-service,speecht5-service,vllm-service,tgi-service,audioqna-xeon-backend-server,audioqna-xeon-ui-server  # additional no proxies if needed
export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
source ./set_env.sh
```

For vLLM inference usage

```bash
export host_ip="External_Public_IP"           # ip address of the node
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip,whisper-service,speecht5-service,vllm-service,tgi-service,audioqna-xeon-backend-server,audioqna-xeon-ui-server  # additional no proxies if needed
export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
source ./set_env_vllm.sh
```

### Deploy the Services Using Docker Compose

To deploy the AudioQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

for TGI inference deployment

```bash
cd docker_compose/amd/gpu/rocm
docker compose -f compose.yaml up -d
```

for vLLM inference deployment

```bash
cd docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml up -d
```

> **Note**: developers should build docker image from source when:
>
> - Developing off the git main branch (as the container's ports in the repo may be different > from the published docker image).
> - Unable to download the docker image.
> - Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| vLLM         | [vLLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/vllm#build-docker)                    |
| LLM          | [LLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/llms)                                                |
| WHISPER      | [Whisper build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/asr/src#211-whisper-server-image)                |
| SPEECHT5     | [SpeechT5 build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/tts/src#211-speecht5-server-image)              |
| GPT-SOVITS   | [GPT-SOVITS build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/gpt-sovits/src#build-the-image) |
| MegaService  | [MegaService build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image)                                     |
| UI           | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                                                 |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

#### For TGI inference deployment

```bash
docker ps -a
```

For the default deployment, the following 5 containers should have started:

```
CONTAINER ID   IMAGE                                                      COMMAND                  CREATED          STATUS          PORTS                                         NAMES
d8007690868d   opea/audioqna:latest                                       "python audioqna.py"     21 seconds ago   Up 19 seconds   0.0.0.0:3008->8888/tcp, [::]:3008->8888/tcp   audioqna-rocm-backend-server
87ba9a1d56ae   ghcr.io/huggingface/text-generation-inference:2.4.1-rocm   "/tgi-entrypoint.sh …"   21 seconds ago   Up 20 seconds   0.0.0.0:3006->80/tcp, [::]:3006->80/tcp       tgi-service
59e869acd742   opea/speecht5:latest                                       "python speecht5_ser…"   21 seconds ago   Up 20 seconds   0.0.0.0:7055->7055/tcp, :::7055->7055/tcp     speecht5-service
0143267a4327   opea/whisper:latest                                        "python whisper_serv…"   21 seconds ago   Up 20 seconds   0.0.0.0:7066->7066/tcp, :::7066->7066/tcp     whisper-service
```

### For vLLM inference deployment

```bash
docker ps -a
```

For the default deployment, the following 5 containers should have started:

```
CONTAINER ID   IMAGE                     COMMAND                  CREATED          STATUS          PORTS                                           NAMES
f3e6893a69fa   opea/audioqna-ui:latest   "docker-entrypoint.s…"   37 seconds ago   Up 35 seconds   0.0.0.0:18039->5173/tcp, [::]:18039->5173/tcp   audioqna-ui-server
f943e5cd21e9   opea/audioqna:latest      "python audioqna.py"     37 seconds ago   Up 35 seconds   0.0.0.0:18038->8888/tcp, [::]:18038->8888/tcp   audioqna-backend-server
074e8c418f52   opea/speecht5:latest      "python speecht5_ser…"   37 seconds ago   Up 36 seconds   0.0.0.0:7055->7055/tcp, :::7055->7055/tcp       speecht5-service
77abe498e427   opea/vllm-rocm:latest     "python3 /workspace/…"   37 seconds ago   Up 36 seconds   0.0.0.0:8081->8011/tcp, [::]:8081->8011/tcp     audioqna-vllm-service
9074a95bb7a6   opea/whisper:latest       "python whisper_serv…"   37 seconds ago   Up 36 seconds   0.0.0.0:7066->7066/tcp, :::7066->7066/tcp       whisper-service
```

If any issues are encountered during deployment, refer to the [Troubleshooting](../../../../README_miscellaneous.md#troubleshooting) section.

### Validate the Pipeline

Once the AudioQnA services are running, test the pipeline using the following command:

```bash
# Test the AudioQnA megaservice by recording a .wav file, encoding the file into the base64 format, and then sending the base64 string to the megaservice endpoint.
# The megaservice will return a spoken response as a base64 string. To listen to the response, decode the base64 string and save it as a .wav file.
wget https://github.com/intel/intel-extension-for-transformers/raw/refs/heads/main/intel_extension_for_transformers/neural_chat/assets/audio/sample_2.wav
base64_audio=$(base64 -w 0 sample_2.wav)

# if you are using speecht5 as the tts service, voice can be "default" or "male"
# if you are using gpt-sovits for the tts service, you can set the reference audio following https://github.com/opea-project/GenAIComps/blob/main/comps/third_parties/gpt-sovits/src/README.md

curl http://${host_ip}:3008/v1/audioqna \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"audio\": \"${base64_audio}\", \"max_tokens\": 64, \"voice\": \"default\"}" \
  | sed 's/^"//;s/"$//' | base64 -d > output.wav
```

**Note** : Access the AudioQnA UI by web browser through this URL: `http://${host_ip}:5173`. Please confirm the `5173` port is opened in the firewall. To validate each microservice used in the pipeline refer to the [Validate Microservices](#validate-microservices) section.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

#### If you use vLLM

```bash
cd ~/audioqna-install/GenAIExamples/AudioQnA/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

#### If you use TGI

```bash
cd ~/audioqna-install/GenAIExamples/AudioQnA/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```

## AudioQnA Docker Compose Files

In the context of deploying an AudioQnA pipeline on an Intel® Xeon® platform, we can pick and choose different large language model serving frameworks, or single English TTS/multi-language TTS component. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                     | Description                                                                               |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- |
| [compose_vllm.yaml](./compose_vllm.yaml) | Default compose file using vllm as serving framework and redis as vector database         |
| [compose.yaml](./compose.yaml)           | The LLM serving framework is TGI. All other configurations remain the same as the default |

### Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "Intel/neural-chat-7b-v3-3t", '\
'"messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 256}'

curl http://${HOST_IP}:${AUDIOQNA_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "chatcmpl-142f34ef35b64a8db3deedd170fed951",
  "object": "chat.completion",
  "created": 1742270316,
  "model": "Intel/neural-chat-7b-v3-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null
    }
  ],
  "usage": { "prompt_tokens": 66, "total_tokens": 322, "completion_tokens": 256, "prompt_tokens_details": null },
  "prompt_logprobs": null
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"What is Deep Learning?",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${AUDIOQNA_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "generated_text": " "
}
```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### Validate MegaServices

Test the AudioQnA megaservice by recording a .wav file, encoding the file into the base64 format, and then sending the
base64 string to the megaservice endpoint. The megaservice will return a spoken response as a base64 string. To listen
to the response, decode the base64 string and save it as a .wav file.

```bash
# voice can be "default" or "male"
curl http://${host_ip}:3008/v1/audioqna \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64, "voice":"default"}' \
  -H 'Content-Type: application/json' | sed 's/^"//;s/"$//' | base64 -d > output.wav
```

### Validate MicroServices

```bash
# whisper service
curl http://${host_ip}:7066/v1/asr \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'

# speecht5 service
curl http://${host_ip}:7055/v1/tts \
  -X POST \
  -d '{"text": "Who are you?"}' \
  -H 'Content-Type: application/json'
```

## Conclusion

This guide should enable developers to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
