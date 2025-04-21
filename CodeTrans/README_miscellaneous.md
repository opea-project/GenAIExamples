# CodeTrans Docker Image Build

## Table of Contents

1. [Build MegaService Docker Image](#build-megaservice-docker-image)
2. [Build UI Docker Image](#build-ui-docker-image)
3. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
4. [Troubleshooting](#troubleshooting)

## Build MegaService Docker Image

To construct the Megaservice of CodeTrans, the [GenAIExamples](https://github.com/opea-project/GenAIExamples.git) repository is utilized. Build Megaservice Docker image via command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeTrans
docker build --no-cache -t opea/codetrans:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

## Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/CodeTrans/ui
docker build -t opea/codetrans-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

## Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if the developer have an access token. In the absence of a HuggingFace access token, the developer can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/CodeTrans/docker_compose/intel/cpu/xeon/README.md#validate-microservices) first. A simple example:

   ```bash
   http_proxy=""
   curl http://${host_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:7777, the port may be allocated by other users, you can modify the `compose.yaml`.
3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.
