# Build and Deploy MultimodalQnA Application on AMD GPU (ROCm)

This document outlines the deployment process for a MultimodalQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD server with ROCm GPUs. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/multimodalqna-install && cd multimodalqna-install
  ```

- #### Clone the repository GenAIExamples (the default repository branch "main" is used here):

  ```bash
  git clone https://github.com/opea-project/GenAIExamples.git
  ```

  If you need to use a specific branch/tag of the GenAIExamples repository, then (v1.3 replace with its own value):

  ```bash
  git clone https://github.com/opea-project/GenAIExamples.git && cd GenAIExamples && git checkout v1.3
  ```

  We remind you that when using a specific version of the code, you need to use the README from this version:

- #### Go to build directory:

  ```bash
  cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_image_build
  ```

- Cleaning up the GenAIComps repository if it was previously cloned in this directory.
  This is necessary if the build was performed earlier and the GenAIComps folder exists and is not empty:

  ```bash
  echo Y | rm -R GenAIComps
  ```

- #### Clone the repository GenAIComps (the default repository branch "main" is used here):

  ```bash
  git clone https://github.com/opea-project/GenAIComps.git
  ```

  If you use a specific tag of the GenAIExamples repository,
  then you should also use the corresponding tag for GenAIComps. (v1.3 replace with its own value):

  ```bash
  git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout v1.3
  ```

  We remind you that when using a specific version of the code, you need to use the README from this version.

- #### Setting the list of images for the build (from the build file.yaml)

  If you want to deploy a vLLM-based or TGI-based application, then the set of services is installed as follows:

  #### vLLM-based application

  ```bash
  service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding retriever lvm dataprep whisper vllm-rocm"
  ```

  #### TGI-based application

  ```bash
  service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding retriever lvm dataprep whisper"
  ```

- #### Optional. Pull TGI Docker Image (Do this if you want to use TGI)

  ```bash
  docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  ```

- #### Build Docker Images

  ```bash
  docker compose -f build.yaml build ${service_list} --no-cache
  ```

  After the build, we check the list of images with the command:

  ```bash
  docker image ls
  ```

  The list of images should include:

  ##### vLLM-based application:

  - opea/vllm-rocm:latest
    - opea/lvm:latest
    - opea/multimodalqna:latest
    - opea/multimodalqna-ui:latest
    - opea/dataprep:latest
    - opea/embedding:latest
    - opea/embedding-multimodal-bridgetower:latest
    - opea/retriever:latest
    - opea/whisper:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.4.1-rocm
    - opea/lvm:latest
    - opea/multimodalqna:latest
    - opea/multimodalqna-ui:latest
    - opea/dataprep:latest
    - opea/embedding:latest
    - opea/embedding-multimodal-bridgetower:latest
    - opea/retriever:latest
    - opea/whisper:latest

---

## Deploy the MultimodalQnA Application

### Docker Compose Configuration for AMD GPUs

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file:

- compose_vllm.yaml - for vLLM-based application
- compose.yaml - for TGI-based

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/:/dev/dri/
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

This configuration forwards all available GPUs to the container. To use a specific GPU, specify its `cardN` and `renderN` device IDs. For example:

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/card0:/dev/dri/card0
  - /dev/dri/renderD128:/dev/dri/renderD128
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

**How to Identify GPU Device IDs:**
Use AMD GPU driver utilities to determine the correct `cardN` and `renderN` IDs for your GPU.

### Set deploy environment variables

#### Setting variables in the operating system environment:

##### Set variable HF_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HF_TOKEN='your_huggingfacehub_token'
```

#### Set variables value in set_env\*\*\*\*.sh file:

Go to Docker Compose directory:

```bash
cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_compose/amd/gpu/rocm
```

The example uses the Nano text editor. You can use any convenient text editor:

#### If you use vLLM

```bash
nano set_env_vllm.sh
```

#### If you use TGI

```bash
nano set_env.sh
```

If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env\*\*\*\*.sh

- **Variables with names like "**\*\*\*\*\*\*\_PORT"\*\* - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env.sh or set_env_vllm they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

#### Required Models

By default, the multimodal-embedding and LVM models are set to a default value as listed below:

| Service   | Model                                       |
| --------- | ------------------------------------------- |
| embedding | BridgeTower/bridgetower-large-itm-mlm-gaudi |
| LVM       | llava-hf/llava-1.5-7b-hf                    |
| LVM       | Xkev/Llama-3.2V-11B-cot                     |

Note:

For AMD ROCm System "Xkev/Llama-3.2V-11B-cot" is recommended to run on ghcr.io/huggingface/text-generation-inference:2.4.1-rocm

#### Set variables with script set_env\*\*\*\*.sh

#### If you use vLLM

```bash
. set_env_vllm.sh
```

#### If you use TGI

```bash
. set_env.sh
```

### Start the services:

#### If you use vLLM

```bash
docker compose -f compose_vllm.yaml up -d
```

#### If you use TGI

```bash
docker compose -f compose.yaml up -d
```

All containers should be running and should not restart:

##### If you use vLLM:

- multimodalqna-vllm-service
- multimodalqna-lvm
- multimodalqna-backend-server
- multimodalqna-gradio-ui-server
- whisper-service
- embedding-multimodal-bridgetower
- redis-vector-db
- embedding
- retriever-redis
- dataprep-multimodal-redis

##### If you use TGI:

- tgi-llava-rocm-server
- multimodalqna-lvm
- multimodalqna-backend-server
- multimodalqna-gradio-ui-server
- whisper-service
- embedding-multimodal-bridgetower
- redis-vector-db
- embedding
- retriever-redis
- dataprep-multimodal-redis

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "Xkev/Llama-3.2V-11B-cot", '\
'"messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 256}'

curl http://${HOST_IP}:${MULTIMODALQNA_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "chatcmpl-a3761920c4034131b3cab073b8e8b841",
  "object": "chat.completion",
  "created": 1742959065,
  "model": "Intel/neural-chat-7b-v3-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": " Deep Learning refers to a modern approach of Artificial Intelligence that aims to replicate the way human brains process information by teaching computers to learn from data without extensive programming",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null
    }
  ],
  "usage": { "prompt_tokens": 15, "total_tokens": 47, "completion_tokens": 32, "prompt_tokens_details": null },
  "prompt_logprobs": null
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"What is Deep Learning?",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${MULTIMODALQNA_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "generated_text": "\n\nDeep Learning is a subset of machine learning, which focuses on developing methods inspired by the functioning of the human brain; more specifically, the way it processes and acquires various types of knowledge and information. To enable deep learning, the networks are composed of multiple processing layers that form a hierarchy, with each layer learning more complex and abstraction levels of data representation.\n\nThe principle of Deep Learning is to emulate the structure of neurons in the human brain to construct artificial neural networks capable to accomplish complicated pattern recognition tasks more effectively and accurately. Therefore, these neural networks contain a series of hierarchical components, where units in earlier layers receive simple inputs and are activated by these inputs. The activation of the units in later layers are the results of multiple nonlinear transformations generated from reconstructing and integrating the information in previous layers. In other words, by combining various pieces of information at each layer, a Deep Learning network can extract the input features that best represent the structure of data, providing their outputs at the last layer or final level of abstraction.\n\nThe main idea of using these 'deep' networks in contrast to regular algorithms is that they are capable of representing hierarchical relationships that exist within the data and learn these representations by"
}
```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate the LVM Service

```bash
curl http://${host_ip}:${MULTIMODALQNA_LVM_PORT}/v1/lvm \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'
```

Checking the response from the service. The response should be similar to JSON:

```textmate
{"downstream_black_list":[],"id":"1b17e903e8c773be909bde0e7cfdb53f","text":" I will analyze the image and provide a detailed description based on its visual characteristics. I will then compare these characteristics to the standard answer provided to ensure accuracy.\n\n1. **Examine the Image**: The image is a solid color, which appears to be a shade of yellow. There are no additional elements or patterns present in the image.\n\n2. **Compare with Standard Answer**: The standard answer describes the image as a \"yellow image\" without any additional details or context. This matches the observed characteristics of the image being a single, uniform yellow color.\n\n3. **Conclusion**: Based on the visual analysis and comparison with the standard answer, the image can be accurately described as a \"yellow image.\" There are no other features or elements present that would alter this description.\n\nFINAL ANSWER: The image is a yellow image.","metadata":{"video_id":"8c7461df-b373-4a00-8696-9a2234359fe0","source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4","time_of_frame_ms":"37000000","transcript_for_inference":"yellow image"}}
```

If the service response has a meaningful response in the value of the "choices.text" key,
then we consider the vLLM service to be successfully launched

### 3. Validate MicroServices

#### embedding-multimodal-bridgetower

Text example:

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example"}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"embedding":[0.036936961114406586,-0.0022056063171476126,0.0891181230545044,-0.019263656809926033,-0.049174826592206955,-0.05129311606287956,-0.07172256708145142,0.04365323856472969,0.03275766223669052,0.0059910244308412075,-0.0301326...,-0.0031989417038857937,0.042092420160770416]}
```

Image example:

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"embedding":[0.024372786283493042,-0.003916610032320023,0.07578050345182419,...,-0.046543147414922714]}
```

#### embedding

Text example:

```bash
curl http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"text" : "This is some sample text."}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"4fb722012a2719e38188190e1cb37ed3","text":"This is some sample text.","embedding":[0.043303076177835464,-0.051807764917612076,...,-0.0005179636646062136,-0.0027774290647357702],"search_type":"similarity","k":4,"distance_threshold":null,"fetch_k":20,"lambda_mult":0.5,"score_threshold":0.2,"constraints":null,"url":null,"base64_image":null}
```

Image example:

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"cce4eab623255c4c632fb920e277dcf7","text":"This is some sample text.","embedding":[0.02613169699907303,-0.049398183822631836,...,0.03544217720627785],"search_type":"similarity","k":4,"distance_threshold":null,"fetch_k":20,"lambda_mult":0.5,"score_threshold":0.2,"constraints":null,"url":"https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true","base64_image":"iVBORw0KGgoAAAANSUhEUgAAAoEAAAJqCAMAAABjDmrLAAAABGdBTUEAALGPC/.../BCU5wghOc4AQnOMEJTnCCE5zgBCc4wQlOcILzqvO/ARWd2ns+lvHkAAAAAElFTkSuQmCC"}
```

#### retriever-multimodal-redis

set "your_embedding" variable:

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
```

Test Redis retriever

```bash
curl http://${host_ip}:${REDIS_RETRIEVER_PORT}/v1/retrieval \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"test\",\"embedding\":${your_embedding}}"
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"80a4f3fc5f5d5cd31ab1e3912f6b6042","retrieved_docs":[],"initial_query":"test","top_n":1,"metadata":[]}
```

#### whisper service

```bash
curl http://${host_ip}:7066/v1/asr \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"asr_result":"you"}
```

### 4. Validate the MegaService

```bash
DATA='{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'

curl http://${HOST_IP}:${MULTIMODALQNA_BACKEND_SERVICE_PORT}/v1/multimodalqna \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"chatcmpl-75aK2KWCfxZmVcfh5tiiHj","object":"chat.completion","created":1743568232,"model":"multimodalqna","choices":[{"index":0,"message":{"role":"assistant","content":"There is no video segments retrieved given the query!"},"finish_reason":"stop","metadata":{"audio":"you"}}],"usage":{"prompt_tokens":0,"total_tokens":0,"completion_tokens":0}}
```

If the output lines in the "choices.text" keys contain words (tokens) containing meaning, then the service is considered launched successfully.

### 5. Stop application

#### If you use vLLM

```bash
cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

#### If you use TGI

```bash
cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```
