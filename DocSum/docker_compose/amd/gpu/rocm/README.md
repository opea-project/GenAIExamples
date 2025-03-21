# Build and Deploy DocSum Application on AMD GPU (ROCm)

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/docsum-install && cd docsum-install
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
  cd ~/docsum-install/GenAIExamples/DocSum/docker_image_build
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
  service_list="docsum docsum-gradio-ui whisper llm-docsum vllm-rocm"
  ```

  #### TGI-based application

  ```bash
  service_list="docsum docsum-gradio-ui whisper llm-docsum"
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
  - opea/llm-docsum:latest
  - opea/whisper:latest
  - opea/docsum:latest
  - opea/docsum-gradio-ui:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  - opea/llm-docsum:latest
  - opea/whisper:latest
  - opea/docsum:latest
  - opea/docsum-gradio-ui:latest

---

## Deploy the DocSum Application

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
  - /dev/dri/render128:/dev/dri/render128
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

##### Set variable HUGGINGFACEHUB_API_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
```

#### Set variables value in set_env\*\*\*\*.sh file:

Go to Docker Compose directory:

```bash
cd ~/docsum-install/GenAIExamples/DocSum/docker_compose/amd/gpu/rocm
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

- docsum-vllm-service
- docsum-llm-server
- whisper-service
- docsum-backend-server
- docsum-ui-server

##### If you use TGI:

- docsum-tgi-service
- docsum-llm-server
- whisper-service
- docsum-backend-server
- docsum-ui-server

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
curl http://${HOST_IP}:${FAQGEN_VLLM_SERVICE_PORT}/v1/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "prompt": "What is a Deep Learning?",
    "max_tokens": 30,
    "temperature": 0
}'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "cmpl-0844e21b824c4472b77f2851a177eca2",
  "object": "text_completion",
  "created": 1742385979,
  "model": "meta-llama/Meta-Llama-3-8B-Instruct",
  "choices": [
    {
      "index": 0,
      "text": " Deep learning is a subset of machine learning that involves the use of artificial neural networks to analyze and interpret data. It is called \"deep\" because it",
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null,
      "prompt_logprobs": null
    }
  ],
  "usage": { "prompt_tokens": 7, "total_tokens": 37, "completion_tokens": 30, "prompt_tokens_details": null }
}
```

If the service response has a meaningful response in the value of the "choices.text" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
curl http://${HOST_IP}:${FAQGEN_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":64, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "generated_text": " In-Depth Explanation\nDeep Learning involves the use of artificial neural networks (ANNs) with multiple layers to analyze and interpret complex data. In this article, we will explore what is deep learning, its types, and how it works.\n\n### What is Deep Learning?\n\nDeep Learning is a subset of Machine Learning that involves"
}
```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate the LLM Service

```bash
curl http://${HOST_IP}:${FAQGEN_LLM_SERVER_PORT}/v1/docsum \
     -X POST \
     -d '{"messages":"What is Deep Learning?"}' \
     -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "1e47daf13a8bc73495dbfd9836eaa7e4",
  "text": " Q: What is Deep Learning?\n         A: Deep Learning is a subset of Machine Learning that involves the use of artificial neural networks to analyze and interpret data. It is called \"deep\" because it involves multiple layers of interconnected nodes or \"neurons\" that process and transform the data.\n\n         Q: What is the main difference between Deep Learning and Machine Learning?\n         A: The main difference between Deep Learning and Machine Learning is the complexity of the models used. Machine Learning models are typically simpler and more linear, while Deep Learning models are more complex and non-linear, allowing them to learn and represent more abstract and nuanced patterns in data.\n\n         Q: What are some common applications of Deep Learning?\n         A: Some common applications of Deep Learning include image and speech recognition, natural language processing, recommender systems, and autonomous vehicles.\n\n         Q: Is Deep Learning a new field?\n         A: Deep Learning is not a new field, but it has gained significant attention and popularity in recent years due to advances in computing power, data storage, and algorithms.\n\n         Q: Can Deep Learning be used for any type of data?\n         A: Deep Learning can be used for any type of data that can be represented as a numerical array, such as images, audio, text, and time series data.\n\n         Q: Is Deep Learning a replacement for traditional Machine Learning?\n         A: No, Deep Learning is not a replacement for traditional Machine Learning. Instead, it is a complementary technology that can be used in conjunction with traditional Machine Learning techniques to solve complex problems.\n\n         Q: What are some of the challenges associated with Deep Learning?\n         A: Some of the challenges associated with Deep Learning include the need for large amounts of data, the risk of overfitting, and the difficulty of interpreting the results of the models.\n\n         Q: Can Deep Learning be used for real-time applications?\n         A: Yes, Deep Learning can be used for real-time applications, such as image and speech recognition, and autonomous vehicles.\n\n         Q: Is Deep Learning a field that requires a lot of mathematical knowledge?\n         A: While some mathematical knowledge is helpful, it is not necessary to have a deep understanding of mathematics to work with Deep Learning. Many Deep Learning libraries and frameworks provide pre-built functions and tools that can be used to implement Deep Learning models.",
  "prompt": "What is Deep Learning?"
}
```

If the service response has a meaningful response in the value of the "text" key,
then we consider the vLLM service to be successfully launched

### 3. Validate the MegaService

```bash
curl http://${HOST_IP}:${FAQGEN_BACKEND_SERVER_PORT}/v1/docsum \
  -H "Content-Type: multipart/form-data" \
  -F "messages=What is Deep Learning?" \
  -F "max_tokens=100" \
  -F "stream=False"
```

Checking the response from the service. The response should be similar to text:

```json
{
  "id": "chatcmpl-tjwp8giP2vyvRRxnqzc3FU",
  "object": "chat.completion",
  "created": 1742386156,
  "model": "docsum",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": " Q: What is Deep Learning?\n         A: Deep Learning is a subset of Machine Learning that involves the use of artificial neural networks to analyze and interpret data. It is called \"deep\" because it involves multiple layers of interconnected nodes or \"neurons\" that process and transform the data.\n\n         Q: What is the main difference between Deep Learning and Machine Learning?\n         A: The main difference between Deep Learning and Machine Learning is the complexity of the models used. Machine Learning models are typically simpler and"
      },
      "finish_reason": "stop",
      "metadata": null
    }
  ],
  "usage": { "prompt_tokens": 0, "total_tokens": 0, "completion_tokens": 0 }
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the MegaService to be successfully launched

### 4. Validate the Frontend (UI)

To access the UI, use the URL - http://${EXTERNAL_HOST_IP}:${FAGGEN_UI_PORT}
A page should open when you click through to this address:

![UI start page](../../../../assets/img/ui-starting-page.png)

If a page of this type has opened, then we believe that the service is running and responding,
and we can proceed to functional UI testing.

For example, let's take the description of water from the Wiki.
Copy the first few paragraphs from the Wiki and put them in the text field and then click Generate FAQs.
After that, a page with the result of the task should open:

![UI result page](../../../../assets/img/ui-result-page.png)

If the result shown on the page is correct, then we consider the verification of the UI service to be successful.

### 5. Stop application

#### If you use vLLM

```bash
cd ~/docsum-install/GenAIExamples/DocSum/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

#### If you use TGI

```bash
cd ~/docsum-install/GenAIExamples/DocSum/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```
