Copyright (C) 2024 Advanced Micro Devices, Inc.

# Deploy SearchQnA application

## 1. Clone repo and build Docker images

### 1.1. Cloning repo

Create an empty directory in home directory and navigate to it:

```bash
mkdir -p ~/searchqna-test && cd ~/searchqna-test
```

Cloning GenAIExamples repo for build Docker images:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
```

### 1.2. Navigate to repo directory and switching to the desired version of the code:

If you are using the main branch, then you do not need to make the transition, the main branch is used by default

```bash
cd ~/searchqna-test/GenAIExamples/SearchQnA/docker_image_build
git clone https://github.com/opea-project/GenAIComps.git
```

If you are using a specific branch or tag, then we perform git checkout to the desired version.

```bash
### Replace "v1.2" with the code version you need (branch or tag)
cd cd ~/searchqna-test/GenAIExamples/SearchQnA/docker_image_build && git checkout v1.2
git clone https://github.com/opea-project/GenAIComps.git
```

### 1.3. Build Docker images repo

#### Build Docker image:

```bash
docker compose -f build.yaml build --no-cache
```

### 1.4. Pull Docker images from Docker Hub

```bash
docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
```

### 1.5. Checking for the necessary Docker images

After assembling the images, you can check their presence in the list of available images using the command:

```bash
docker image ls
```

The output of the command should contain images:

- ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
- opea/embedding:latest
- opea/web-retriever:latest
- opea/reranking:latest
- opea/llm-vllm-rocm:latest
- opea/llm-textgen:latest
- opea/searchqna:latest
- opea/searchqna-ui:latest

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variables:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
### Replace the string 'your_google_api_key' with your GOOGLE API KEY.
export GOOGLE_API_KEY='your_google_api_key'
### Replace the string 'your_google_cse_id' with your GOOGLE CSE identifier.
export GOOGLE_CSE_ID='your_google_cse_id'
```

### Setting variables in the file set_env_vllm.sh

```bash
cd cd cd ~/searchqna-test/GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm
### The example uses the Nano text editor. You can use any convenient text editor
nano set_env_vllm.sh
```

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env_vllm.sh

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file **launch_agent_service_vllm_rocm.sh** they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

## 3. Deploy application

### 3.1. Deploying applications using Docker Compose

```bash
cd cd ~/searchqna-test/GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm/
docker compose -f compose_vllm up -d
```

After starting the containers, you need to view their status with the command:

```bash
docker ps
```

The following containers should be running:

- search-web-retriever-server
- search-vllm-service
- search-tei-embedding-server
- search-tei-reranking-server
- search-reranking-server
- search-embedding-server
- search-llm-server
- search-backend-server
- search-ui-server

Containers should not restart.

#### 3.1.1. Configuring GPU forwarding

By default, in the Docker Compose file, compose_vllm.yaml is configured to forward all GPUs to the search-vllm-service container.
To use certain GPUs, you need to configure the forwarding of certain devices from the host system to the container.
The configuration must be done in:

```yaml
services:
  #######
  vllm-service:
    devices:
```

Example for set isolation for 1 GPU

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
```

Example for set isolation for 2 GPUs

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /dev/dri/card1:/dev/dri/card1
      - /dev/dri/renderD129:/dev/dri/renderD129
```

### 3.2. Checking the application services

#### 3.2.1. Checking vllm-service

Verification is performed in two ways:

- Checking the container logs

  ```bash
  docker logs search-vllm-service
  ```

  A message like this should appear in the logs:

  ```textmate
  INFO:     Started server process [1]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8011 (Press CTRL+C to quit)
  ```

- Сhecking the response from the service
  ```bash
  ### curl request
  ### Replace 18110 with the value set in the startup script in the variable VLLM_SERVICE_PORT
  curl http://${HOST_IP}:${SEARCH_VLLM_SERVICE_PORT}/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
      "model": "Intel/neural-chat-7b-v3-3",
      "prompt": "What is a Deep Learning?",
      "max_tokens": 30,
      "temperature": 0
  }'
  ```
  The response from the service must be in the form of JSON:
  ```json
  {
    "id": "cmpl-1d7d175d36d0491cba3abaa8b5bd6991",
    "object": "text_completion",
    "created": 1740411135,
    "model": "Intel/neural-chat-7b-v3-3",
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
  The value of "choice.text" must contain a response from the service that makes sense.
  If such a response is present, then the search-vllm-service is considered verified.

#### 3.2.2. Checking search-llm

Сhecking the response from the service

```bash
curl http://${HOST_IP}:${SEARCH_LLM_SERVICE_PORT}/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"stream":true}' \
  -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```textmate
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"\n","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"\n","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"Deep","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" Learning","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" is","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" a","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" subset","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" of","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" Machine","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" Learning","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" that","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" is","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" concerned","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" with","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" algorithms","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" inspired","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-ee61c243a172423d836f78cfddb63b93","choices":[{"finish_reason":"length","index":0,"logprobs":null,"text":" by","stop_reason":null}],"created":1741715027,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

The value of "choices.text" must contain a response from the service that makes sense.
If such a response is present, then the search-llm is considered verified.

#### 3.2.3. Checking search-tei-embedding-service

Сhecking the response from the service

```bash
curl http://${HOST_IP}:${SEARCH_TEI_EMBEDDING_PORT}/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

The response from the service must be in the form of text:

```textmate
[[0.00037115702,-0.06356819,0.0024758505,........-0.08894698,0.045917906,-0.00475913,0.034920968,-0.0064531155,-0.00689886,-0.06119457,0.021173967,-0.027787622,-0.02472986,0.03998034,0.03737826,-0.0067949123,0.022558564,-0.04570635,-0.033072025,0.022725677,0.016026087,-0.02125421,-0.02984927,-0.0049473033]]
```

If the output value is similar to the example given, we consider the service to be successfully launched.

#### 3.2.4. Checking search-embedding

Сhecking the response from the service

```bash
curl http://${HOST_IP}:${SEARCH_EMBEDDING_SERVICE_PORT}/v1/embeddings\
  -X POST \
  -d '{"input":"hello"}' \
  -H 'Content-Type: application/json'
```

The response from the service must be in the form of text:

```json
{
  "object": "list",
  "model": "BAAI/bge-base-en-v1.5",
  "data": [
    {
      "index": 0,
      "object": "embedding",
      "embedding": [0.0007791813, 0.042613804, 0.020304274, -0.0070378557, 0.059366036, -0.0044034636]
    }
  ],
  "usage": { "prompt_tokens": 3, "total_tokens": 3, "completion_tokens": 0 }
}
```

If the output value is similar to the example given, we consider the service to be successfully launched.

#### 3.2.5. Checking search-web-retriever

Сhecking the response from the service

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${HOST_IP}:${SEARCH_WEB_RETRIEVER_SERVICE_PORT}/v1/web_retrieval \
  -X POST \
  -d "{\"text\":\"What is the 2024 holiday schedule?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```json
{
  "id": "67cace517e36aff3f10a756b87a9125b",
  "retrieved_docs": [
    {
      "downstream_black_list": [],
      "id": "4ba6bc05cff877011da321bbd03c05a8",
      "text": "* Message from the Director\n    * Introduction\n    * Workforce Planning and AnalysisToggle submenu\n      * Early Career Talent\n    * Evaluation System Development\n    * Innovation\n    * Leading Practices\n    * Resources\n  * Career Paths for Federal Program and Project Management GuideToggle submenu\n    * Introduction\n    * Purpose and Objectives\n    * Data and Methodology\n    * Differentiating Job Titles for Program and Project Managers\n    * Understanding the Career Path\n    * Success Factors\n    * Competency Development Framework Part I\n    * Competency Development Framework Part II\n    * Credentials and Certifications\n    * Appendix A: Key Terminology\n    * Appendix B: Subject Matter Expert (SME) Workshops List of Participating Agencies\n    * Appendix C: List of Designated Title & Number for Each Job Series\n    * Appendix D: Program and Project Competency Model and Competency Definitions\n    * Appendix E: Program and Project Management Competency Model Proficiency Level\n  * FY 2024 Human Capital ReviewsToggle submenu\n    * Message from the Director\n    * Introduction\n    * Data Driven Decision Making\n    * Strategic Planning\n    * Artificial Intelligence\n    * Resources \n description: Welcome to opm.gov \n \n title: Federal Holidays \n \n source: https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/ \n"
    },
    {
      "downstream_black_list": [],
      "id": "b3908b0a74cb115a09a0928beda79bc5",
      "text": "If you have a question whether a particular State office is open or closed,\nplease contact that office.\n\nBack to Top\n\nCommissioner Beth Fastiggi  \n120 State Street, Montpelier, VT 05620  \n(802) 828-3491  \nDHR.General@vermont.gov\n\n_Contact Us  \nHR Field Representative Locator_  \n_Alerts/Closings/Delays_  \nCurrent Road & Driving Conditions  \nPublic Records Officer Contact Information and Public Records Database  \nTransparent and Open Government Information​\n\n### Connect with Us\n\nTwitter\n\nFacebook\n\nInstagram\n\nYouTube\n\nRSS\n\n## Need Assistance?\n\nClick here for a list of Department contacts.\n\n\n\n## How Do I?\n\n    * Learn about benefit plans\n    * Contact EAP\n    * Answer payroll questions\n    * See pay periods & pay dates\n    * Find wellness programs\n    * Learn about leave benefits\n    * Make a public records request\n    * Find info about classification\n    * OWA Email Login\n    * Find workforce reports\n    * View Workforce Dashboard\n    * Employment Verification\n\n## Popular Links\n\n    * Classroom/Online Training\n    * Collective Bargaining Agreements\n    * Employee/Manager Self Service\n    * Job Specifications\n    * Pay Charts\n    * Pay Dates\n    * Policy & Procedure Manual\n    * Retirement Planning\n    * Retirement Office \n    * State Holiday Schedule\n    * Time Entry & Approval\n    * VTHR Login\n\n__\n\nReturn to top\n\nCopyright (C) 2025 State of Vermont All rights reserved. | \n\n    * Policies\n    * Accessibility Policy\n    * Privacy Policy\n    * Feedback Survey  \n title: State Holiday Schedule | Department of Human Resources \n \n source: https://humanresources.vermont.gov/benefits-wellness/holiday-schedule \n"
    },
    {
      "downstream_black_list": [],
      "id": "b52e0a8865ebfc6f93cc5e366e9b57b0",
      "text": "##  Revenue and Spending\n\n    * Contracts \n    * Monthly Revenue Watch\n    * Severance Taxes\n    * Sources of Revenue Guide\n    * Taxes of Texas: A Field Guide (PDF)\n\n##  Budget and  \nFinance\n\n    * Financial Reports and Forecasts\n    * Budget Process Primer\n    * Texas Investments\n    * Understanding the ACFR\n    * Cash Report and ACFR (PDF)\n\n##  Open Data Tools and Information\n\n    * Analysis and Reports\n    * Dashboards\n    * Pension Search Tool\n    * Search Datasets\n    * Secure Information and File Transfer (SIFT)\n\n##  Local Governments\n\n    * Eminent Domain\n    * Hotel Occupancy Tax\n    * Local Government Debt\n    * Sheriffs' and Constables' Fees\n    * SPD Financials and Taxes \n    * Tax Allocation Summaries\n    * Transparency Stars\n    * Reports and Tools\n\n  * Economy\n\n##  __  Economy Home\n\n##  Fiscal Notes\n\n    * Latest Articles\n    * Archives\n    * About _Fiscal Notes_\n    * Republish\n\n##  In Depth\n\n    * Regional Reports\n    * Forecasts\n    * Key Economic Indicators\n    * Economic Data(Good for Texas Tours)\n    * Special Reports\n\n##  Economic Development Programs\n\n    * Property Tax Programs\n    * Sales Tax Programs\n    * Grants and Special Assessments\n    * Search Tools and Data\n\n  * Purchasing\n\n##  __  Purchasing Home\n\n## Statewide Contracts\n\n    * Search Statewide Contracts\n    * Contract Development\n    * Contract Management\n    * Procurement Oversight & Delegation\n    * Texas Multiple Award Schedule (TXMAS)\n    * txsmartbuy.gov\n    * DIR Contracts \n description: Office holiday schedule for fiscal 2024. \n \n title: State of Texas Holiday Schedule - Fiscal 2025 \n \n source: https://comptroller.texas.gov/about/holidays.php \n"
    },
    {
      "downstream_black_list": [],
      "id": "ee75f07d60742868abfae486bbc1849d",
      "text": "Skip to page navigation\n\nAn official website of the United States government\n\nHere's how you know\n\nHere's how you know\n\n**Official websites use .gov**  \nA **.gov** website belongs to an official government organization in the\nUnited States.\n\n**Secure .gov websites use HTTPS**  \nA **lock** (  Lock A locked padlock ) or **https://** means you’ve safely\nconnected to the .gov website. Share sensitive information only on official,\nsecure websites.\n\nMenu\n\nSearch all of OPM Submit\n\nSections\n\n  * About Toggle submenu\n\n    * Our Agency\n    * Who We Are\n    * Our Work\n    * Mission & History\n    * Careers at OPM\n    * Doing Business with OPM\n    * Reports & Publications\n    * Open Government\n    * Get Help\n    * Contact Us\n    * News\n    * Data\n    * 2023 Agency Financial Report\n    * Combined Federal Campaign\n    * 2023 Annual Performance Report\n    * FY 2025 Congressional Budget Justification\n    * 2024 Agency Financial Report\n    * 2024 Annual Performance Report\n\n  * Policy Toggle submenu \n description: Welcome to opm.gov \n \n title: Federal Holidays \n \n source: https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/ \n"
    }
  ],
  "initial_query": "What is the 2024 holiday schedule?",
  "top_n": 1
}
```

The value of "retrieved_docs.text" must contain a response from the service that makes sense.
If such a response is present, then the search-web-retriever is considered verified.

#### 3.2.6. Checking search-tei-reranking-service

Сhecking the response from the service

```bash
curl http://${HOST_IP}:${SEARCH_TEI_RERANKING_PORT}/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```json
[
  { "index": 1, "score": 0.94238955 },
  { "index": 0, "score": 0.120219156 }
]
```

If the output value is similar to the example given, we consider the service to be successfully launched.

#### 3.2.7. Checking search-reranking

Сhecking the response from the service

```bash
curl http://${HOST_IP}:${SEARCH_RERANK_SERVICE_PORT}/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```json
{
  "id": "26e5d7f6259b8a184387f13fc9c54038",
  "model": null,
  "query": "What is Deep Learning?",
  "max_tokens": 1024,
  "max_new_tokens": 1024,
  "top_k": 10,
  "top_p": 0.95,
  "typical_p": 0.95,
  "temperature": 0.01,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "repetition_penalty": 1.03,
  "stream": true,
  "language": "auto",
  "chat_template": null,
  "documents": ["Deep learning is..."]
}
```

If the output value is similar to the example given, we consider the service to be successfully launched.

#### 3.2.8. Checking search-backend-server

Сhecking the response from the service

```bash
curl http://${HOST_IP}:${SEARCH_BACKEND_SERVICE_PORT}/v1/searchqna -H "Content-Type: application/json" -d '{
     "messages": "What is the latest news? Give me also the source link.",
     "stream": "True"
     }'
```

The response from the service must be in the form of JSON:

```textmate
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"\n","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"   ","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" View","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" the","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" latest","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" news","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":".","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
.......
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"com","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"/","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-602c2cd2745c4095ad8957f7e5ed8ca7","choices":[{"finish_reason":"stop","index":0,"logprobs":null,"text":"","stop_reason":null}],"created":1741716737,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

If the output value is similar to the example given, we consider the service to be successfully launched.
