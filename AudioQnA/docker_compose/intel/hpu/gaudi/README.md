# Deploying AudioQnA on Intel® Gaudi® Processors

This document outlines the single node deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on Intel Gaudi server. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.

Note: The default LLM is `meta-llama/Meta-Llama-3-8B-Instruct`. Before deploying the application, please make sure either you've requested and been granted the access to it on [Huggingface](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) or you've downloaded the model locally from [ModelScope](https://www.modelscope.cn/models).

## Table of Contents

1. [AudioQnA Quick Start Deployment](#audioqna-quick-start-deployment)
2. [AudioQnA Docker Compose Files](#audioqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## AudioQnA Quick Start Deployment

This section describes how to quickly deploy and test the AudioQnA service manually on an Intel® Gaudi® processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the AudioQnA Intel® Gaudi® platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA
```

Then checkout a released version, such as v1.2:

```bash
git checkout v1.2
```

### Configure the Deployment Environment

To set up environment variables for deploying AudioQnA services, set up some parameters specific to the deployment environment and source the `set_env.sh` script in this directory:

```bash
export host_ip="External_Public_IP"           # ip address of the node
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip,whisper-service,speecht5-service,vllm-service,tgi-service,audioqna-gaudi-backend-server,audioqna-gaudi-ui-server  # additional no proxies if needed
export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
source ./set_env.sh
```

Consult the section on [AudioQnA Service configuration](#audioqna-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the AudioQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
cd docker_compose/intel/hpu/gaudi
docker compose -f compose.yaml up -d
```

> **Note**: developers should build docker image from source when:
>
> - Developing off the git main branch (as the container's ports in the repo may be different > from the published docker image).
> - Unable to download the docker image.
> - Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------------------------------- |
| vLLM-gaudi   | [vLLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/vllm#build-docker-1)     |
| LLM          | [LLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/llms)                                   |
| WHISPER      | [Whisper build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/asr/src#211-whisper-server-image)   |
| SPEECHT5     | [SpeechT5 build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/tts/src#211-speecht5-server-image) |
| MegaService  | [MegaService build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image)                        |
| UI           | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                                    |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment, the following 5 containers should have started:

```
23f27dab14a5   opea/whisper-gaudi:latest                                                                   "python whisper_serv…"   18 minutes ago   Up 18 minutes             0.0.0.0:7066->7066/tcp, :::7066->7066/tcp                                              whisper-service
629da06b7fb2   opea/audioqna-ui:latest                                                                     "docker-entrypoint.s…"   19 minutes ago   Up 18 minutes             0.0.0.0:5173->5173/tcp, :::5173->5173/tcp                                              audioqna-gaudi-ui-server
8a74d9806b87   opea/audioqna:latest                                                                        "python audioqna.py"     19 minutes ago   Up 18 minutes             0.0.0.0:3008->8888/tcp, [::]:3008->8888/tcp                                            audioqna-gaudi-backend-server
29324430f42e   opea/vllm-gaudi:latest                                                                      "python3 -m vllm.ent…"   19 minutes ago   Up 19 minutes (healthy)   0.0.0.0:3006->80/tcp, [::]:3006->80/tcp                                                vllm-gaudi-service
dbd585f0a95a   opea/speecht5-gaudi:latest                                                                  "python speecht5_ser…"   19 minutes ago   Up 19 minutes             0.0.0.0:7055->7055/tcp, :::7055->7055/tcp                                              speecht5-service
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

curl http://${host_ip}:3008/v1/audioqna \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"audio\": \"${base64_audio}\", \"max_tokens\": 64, \"voice\": \"default\"}" \
  | sed 's/^"//;s/"$//' | base64 -d > output.wav
```

**Note** : Access the AudioQnA UI by web browser through this URL: `http://${host_ip}:5173`. Please confirm the `5173` port is opened in the firewall. To validate each microservice used in the pipeline refer to the [Validate Microservices](#validate-microservices) section.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```

## AudioQnA Docker Compose Files

In the context of deploying an AudioQnA pipeline on an Intel® Gaudi® platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                   | Description                                                                               |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)         | Default compose file using vllm as serving framework and redis as vector database         |
| [compose_tgi.yaml](./compose_tgi.yaml) | The LLM serving framework is TGI. All other configurations remain the same as the default |

## Validate MicroServices

1. Whisper Service

   ```bash
   wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav
   curl http://${host_ip}:${WHISPER_SERVER_PORT}/v1/audio/transcriptions \
     -H "Content-Type: multipart/form-data" \
     -F file="@./sample.wav" \
     -F model="openai/whisper-small"
   ```

2. LLM backend Service

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready and the container (`vllm-service` or `tgi-service`) status shown via `docker ps` will be `healthy`. Before that, the status will be `health: starting`.

   Or try the command below to check whether the LLM serving is ready.

   ```bash
   # vLLM service
   docker logs vllm-service 2>&1 | grep complete
   # If the service is ready, you will get the response like below.
   INFO:     Application startup complete.
   ```

   ```bash
   # TGI service
   docker logs tgi-service | grep Connected
   # If the service is ready, you will get the response like below.
   2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
   ```

   Then try the `cURL` command below to validate services.

   ```bash
   # either vLLM or TGI service
   curl http://${host_ip}:${LLM_SERVER_PORT}/v1/chat/completions \
     -X POST \
     -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
     -H 'Content-Type: application/json'
   ```

3. TTS Service

   ```bash
   # speecht5 service
   curl http://${host_ip}:${SPEECHT5_SERVER_PORT}/v1/audio/speech -XPOST -d '{"input": "Who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
   ```

## Conclusion

This guide should enable developers to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
