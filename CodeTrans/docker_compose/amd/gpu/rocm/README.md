# Build and Deploy CodeTrans Application on AMD GPU (ROCm)

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/codetrans-install && cd codetrans-install
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
  cd ~/codetrans-install/GenAIExamples/CodeTrans/docker_image_build
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
  service_list="vllm-rocm llm-textgen codetrans codetrans-ui nginx"
  ```

  #### TGI-based application

  ```bash
  service_list="llm-textgen codetrans codetrans-ui nginx"
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
  - opea/llm-textgen:latest
  - opea/codetrans:latest
  - opea/codetrans-ui:latest
  - opea/nginx:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  - opea/llm-textgen:latest
  - opea/codetrans:latest
  - opea/codetrans-ui:latest
  - opea/nginx:latest

---

## Deploy the CodeTrans Application

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
cd ~/codetrans-install/GenAIExamples/CodeTrans/docker_compose/amd/gpu/rocm
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

- codetrans-vllm-service
- codetrans-llm-server
- codetrans-backend-server
- codetrans-ui-server
- codetrans-nginx-server

##### If you use TGI:

- codetrans-tgi-service
- codetrans-llm-server
- codetrans-backend-server
- codetrans-ui-server
- codetrans-nginx-server

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}' \

curl http://${HOST_IP}:${CODETRANS_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "chatcmpl-9080fdc16f0f4f43a4e1b0de1e29af1f",
  "object": "chat.completion",
  "created": 1742286287,
  "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Deep Learning is a subset of Machine Learning that encompasses a wide range of algorithms and models",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null
    }
  ],
  "usage": { "prompt_tokens": 34, "total_tokens": 51, "completion_tokens": 17, "prompt_tokens_details": null },
  "prompt_logprobs": null
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"Implement a high-level API for a TODO list application. '\
'The API takes as input an operation request and updates the TODO list in place. '\
'If the request is invalid, raise an exception.",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${CODEGEN_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

````json
{
  "generated_text": " The supported operations are \"add_task\", \"complete_task\", and \"remove_task\". Each operation can be defined with a corresponding function in the API.\n\nAdd your API in the following format:\n\n```\nTODO App API\n\nsupported operations:\n\noperation name           description\n-----------------------  ------------------------------------------------\n<operation_name>         <operation description>\n```\n\nUse type hints for function parameters and return values. Specify a text description of the API's supported operations.\n\nUse the following code snippet as a starting point for your high-level API function:\n\n```\nclass TodoAPI:\n    def __init__(self, tasks: List[str]):\n        self.tasks = tasks  # List of tasks to manage\n\n    def add_task(self, task: str) -> None:\n        self.tasks.append(task)\n\n    def complete_task(self, task: str) -> None:\n        self.tasks = [t for t in self.tasks if t != task]\n\n    def remove_task(self, task: str) -> None:\n        self.tasks = [t for t in self.tasks if t != task]\n\n    def handle_request(self, request: Dict[str, str]) -> None:\n        operation = request.get('operation')\n        if operation == 'add_task':\n            self.add_task(request.get('task'))\n        elif"
}
````

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate the LLM Service

```bash
DATA='{"query":"    ### System: Please translate the following Python codes into  Java codes.    '\
'### Original codes:    '\'''\'''\''Python    \nprint(\"Hello, World!\");\n    '\'''\'''\''    '\
'### Translated codes:"}'

curl http://${HOST_IP}:${CODETRANS_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```textmate
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"   ","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" ###","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" Java","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"\n","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":".out","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":".println","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"(\"","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"Hello","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":",","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" World","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"!\");","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-c2acd8c385be4f59bae01d1ec31ca617","choices":[{"finish_reason":"stop","index":0,"logprobs":null,"text":"","stop_reason":null}],"created":1742287740,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

If the service response has a meaningful response in the value of the "choices.text" key,
then we consider the vLLM service to be successfully launched

### 3. Validate the MegaService

```bash
DATA='{"language_from": "Python","language_to": "Java","source_code": '\
'"print(\"Hello, World!\");\n}"}'

curl http://${HOST_IP}:${CODETRANS_BACKEND_SERVICE_PORT}/v1/codetrans \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

Checking the response from the service. The response should be similar to text:

```textmate
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"Java","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
..............
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"\n","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"        ","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" public","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" class","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" HelloWorld","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" {\n","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-b63a51caccd34687b26614eb46c0abc6","choices":[{"finish_reason":"length","index":0,"logprobs":null,"text":"            ","stop_reason":null}],"created":1742287989,"model":"Qwen/Qwen2.5-Coder-7B-Instruct","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

If the output lines in the "choices.text" keys contain words (tokens) containing meaning, then the service is considered launched successfully.

### 4. Validate the Frontend (UI)

To access the UI, use the URL - http://${EXTERNAL_HOST_IP}:${CODETRANS_NGINX_PORT}
A page should open when you click through to this address:

![UI start page](../../../../assets/img/ui-starting-page.png)

If a page of this type has opened, then we believe that the service is running and responding,
and we can proceed to functional UI testing.

For example, let's choose the translation of code from Python to Java.
Enter the code 'print("hello world!")' in the Python field.
After that, a page with the result of the task should open:

![UI result page](../../../../assets/img/ui-result-page.png)

If the result shown on the page is correct, then we consider the verification of the UI service to be successful.

### 5. Stop application

#### If you use vLLM

```bash
cd ~/codetrans-install/GenAIExamples/CodeTrans/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

#### If you use TGI

```bash
cd ~/codetrans-install/GenAIExamples/CodeTrans/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```
