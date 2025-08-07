# Deploying AudioQnA on AMD EPYC™ Processors

This document provides a step-by-step guide for deploying the AudioQnA application on a single node, leveraging the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices, optimized for AMD EPYC™ Processors. The process covers pulling Docker images, deploying containers using Docker Compose, and running services with the `llm` microservices.

Note: The default LLM is `meta-llama/Meta-Llama-3-8B-Instruct`. Before deploying the application, please make sure either you've requested and been granted the access to it on [Huggingface](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) or you've downloaded the model locally from [ModelScope](https://www.modelscope.cn/models).

## Table of Contents

1. [AudioQnA Quick Start Deployment](#audioqna-quick-start-deployment)
2. [AudioQnA Docker Compose Files](#audioqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## AudioQnA Quick Start Deployment

This section describes how to quickly deploy and test the AudioQnA service manually on an AMD EPYC™ processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Install Docker](#install-docker)
3. [Determine your host's external IP address](#determine-your-host-external-ip-address)
4. [Configure the Deployment Environment](#configure-the-deployment-environment)
5. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
6. [Check the Deployment Status](#check-the-deployment-status)
7. [Validate the Pipeline](#validate-the-pipeline)
8. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the AudioQnA AMD EPYC™ platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA/docker_compose/amd/cpu/epyc

```

### Install Docker

Ensure Docker is installed on your system. If Docker is not already installed, use the provided script to set it up:

    source ./install_docker.sh

This script installs Docker and its dependencies. After running it, verify the installation by checking the Docker version:

    docker --version

If Docker is already installed, this step can be skipped.

### Determine your host external IP address

Run the following command in your terminal to list network interfaces:

    ifconfig

Look for the inet address associated with your active network interface (e.g., enp99s0). For example:

    enp99s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.101.16.119  netmask 255.255.255.0  broadcast 10.101.16.255

In this example, the (`host_ip`) would be (`10.101.16.119`).

    # Replace with your host's external IP address
    export host_ip="your_external_ip_address"

### Configure the Deployment Environment

The model_cache directory, by default, stores models in the ./data directory. To change this, use the following command:

```bash
# Optional
export model_cache=/home/documentation/data_audioqna/data # Path to save cache models
```

To set up environment variables for deploying AudioQnA services, set up some parameters specific to the deployment environment and source the `set_env.sh` script in this directory:

```bash
export HF_TOKEN="Your_HuggingFace_API_Token"
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip,whisper-service,speecht5-service,vllm-service,tgi-service,audioqna-epyc-backend-server,audioqna-epyc-ui-server  # additional no proxies if needed
export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
source ./set_env.sh
```

### Deploy the Services Using Docker Compose

To deploy the AudioQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
docker compose -f compose.yaml up -d
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

```bash
docker ps -a
```

For the default deployment, the following 5 containers should have started:

```
1c67e44c39d2   opea/audioqna-ui:latest   "docker-entrypoint.s…"   About a minute ago   Up About a minute             0.0.0.0:5173->5173/tcp, :::5173->5173/tcp   audioqna-epyc-ui-server
833a42677247   opea/audioqna:latest      "python audioqna.py"     About a minute ago   Up About a minute             0.0.0.0:3008->8888/tcp, :::3008->8888/tcp   audioqna-epyc-backend-server
5dc4eb9bf499   opea/speecht5:latest      "python speecht5_ser…"   About a minute ago   Up About a minute             0.0.0.0:7055->7055/tcp, :::7055->7055/tcp   speecht5-service
814e6efb1166   opea/vllm:latest          "python3 -m vllm.ent…"   About a minute ago   Up About a minute (healthy)   0.0.0.0:3006->80/tcp, :::3006->80/tcp       vllm-service
46f7a00f4612   opea/whisper:latest       "python whisper_serv…"   About a minute ago   Up About a minute             0.0.0.0:7066->7066/tcp, :::7066->7066/tcp   whisper-service
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

```bash
docker compose -f compose.yaml down
```

## AudioQnA Docker Compose Files

When deploying an AudioQnA pipeline on an AMD EPYC™ platform, users can select from various large language model serving frameworks or opt for either single-language English TTS. The table below highlights the available configurations included in the application. These configurations serve as templates and can be extended to incorporate additional components from [GenAIComps](https://github.com/opea-project/GenAIComps.git).

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

   During the initial startup, the service requires additional time to download, load, and warm up the model. Once this process is complete, the service will be ready, and the container (either `vllm-service` or `tgi-service`) will display a `healthy` status when viewed using `docker ps`. Prior to this, the status will appear as `health: starting`.

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

   # gpt-sovits service (optional)
   curl http://${host_ip}:${GPT_SOVITS_SERVER_PORT}/v1/audio/speech -XPOST -d '{"input": "Who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
   ```

### Profile Microservices

To further analyze MicroService Performance, users could follow the instructions to profile MicroServices.

#### 1. vLLM backend Service

Users could follow previous section to testing vLLM microservice or CodeGen MegaService. By default, vLLM profiling is not enabled. Users could start and stop profiling by following commands.

##### Start vLLM profiling

```bash
curl http://${host_ip}:${LLM_SERVER_PORT}/start_profile \
    -X POST \
    -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct"}' \
    -H 'Content-Type: application/json'
```

After vLLM profiling is started, users could start asking questions and get responses from vLLM MicroService

```bash
curl http://${host_ip}:${LLM_SERVER_PORT}/v1/chat/completions \
    -X POST \
    -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
    -H 'Content-Type: application/json'
```

##### Stop vLLM profiling

By following command, users could stop vLLM profiling and generate a \*.pt.trace.json.gz file as profiling result under /mnt folder in vllm-service docker instance.

```bash
curl http://${host_ip}:${LLM_SERVER_PORT}/stop_profile \
     -X POST \
     -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct"}' \
     -H 'Content-Type: application/json'
```

After vllm profiling is stopped, users could use below command to get the \*.pt.trace.json.gz file under /mnt folder.

```bash
docker cp  vllm-service:/mnt/ .
```

##### Check profiling result

Open a web browser and type "chrome://tracing" or "ui.perfetto.dev", and then load the json.gz file.

## Conclusion

This guide should enable developers to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
