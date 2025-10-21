# Browser-use Agent Application

Browser-use agent empowers anyone to automate repetitive web tasks. It controls your web browser to perform tasks like visiting websites and extracting data. The application is powered by [browser-use](https://github.com/browser-use/browser-use) and OPEA LLM serving microservice.

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

| Category               | Deployment Option      | Description                                                       |
| ---------------------- | ---------------------- | ----------------------------------------------------------------- |
| On-premise Deployments | Docker Compose (Gaudi) | [Deployment on Gaudi](./docker_compose/intel/hpu/gaudi/README.md) |

## Validated Configurations

| **Deploy Method** | **LLM Engine** | **LLM Model**                | **Hardware** |
| ----------------- | -------------- | ---------------------------- | ------------ |
| Docker Compose    | vLLM           | Qwen/Qwen2.5-VL-32B-Instruct | Intel Gaudi  |
| Docker Compose    | vLLM           | Qwen/Qwen2.5-VL-72B-Instruct | Intel Gaudi  |
