# Code Translation Application

Code translation is the process of converting code written in one programming language to another programming language while maintaining the same functionality. This process is also known as code conversion, source-to-source translation, or transpilation. Code translation is often performed when developers want to take advantage of new programming languages, improve code performance, or maintain legacy systems. Some common examples include translating code from Python to Java, or from JavaScript to TypeScript.

The workflow falls into the following architecture:

![architecture](./assets/img/code_trans_architecture.png)

This Code Translation use case uses Text Generation Inference on Intel Gaudi2 or Intel Xeon Scalable Processor. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products) for more details.

# Deploy Code Translation Service

The Code Translation service can be effortlessly deployed on either Intel Gaudi2 or Intel Xeon Scalable Processor.

Currently we support two ways of deploying Code Translation services on docker:

1. Start services using the docker image on `docker hub`:

```bash
docker pull opea/codetrans:latest
```

2. Start services using the docker images `built from source`: [Guide](./docker)

## Setup Environment Variable

To set up environment variables for deploying Code Translation services, follow these steps:

1. Set the required environment variables:

```bash
export host_ip="External_Public_IP"
export no_proxy="Your_No_Proxy"
```

2. If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
```

3. Set up other environment variables:

```bash
bash ./docker/set_env.sh
```

## Deploy with Docker

### Deploy Code Translation on Gaudi

- If your version of `Habana Driver` < 1.16.0 (check with `hl-smi`), run the following command directly to start Code Translation services. Please find corresponding [docker_compose.yaml](./docker/gaudi/docker_compose.yaml).

```bash
cd GenAIExamples/CodeTrans/docker/gaudi
docker compose -f docker_compose.yaml up -d
```

- If your version of `Habana Driver` >= 1.16.0, refer to the [Gaudi Guide](./docker/gaudi/README.md) to build docker images from source.

### Deploy Code Translation on Xeon

Please find corresponding [docker_compose.yaml](./docker/xeon/docker_compose.yaml).

```bash
cd GenAIExamples/CodeTrans/docker/xeon
docker compose -f docker_compose.yaml up -d
```

Refer to the [Xeon Guide](./docker/xeon/README.md) for more instructions on building docker images from source.

## Deploy with Kubernetes

Please refer to the [Code Translation Kubernetes Guide](./kubernetes/README.md)

# Consume Code Translation Service

Two ways of consuming Code Translation Service:

1. Use cURL command on terminal

```bash
curl http://${host_ip}:7777/v1/codetrans \
    -H "Content-Type: application/json" \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```

2. Access via frontend

To access the frontend, open the following URL in your browser: http://{host_ip}:5173.

By default, the UI runs on port 5173 internally.

# Troubleshooting

1. If you get errors like "Access Denied", please [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/CodeTrans/docker/xeon#validate-microservices) first. A simple example:

```bash
http_proxy=""
curl http://${host_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. (Docker only) If all microservices work well, please check the port ${host_ip}:7777, the port may be allocated by other users, you can modify the `docker_compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", please change container name in `docker_compose.yaml`.
