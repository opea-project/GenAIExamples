# ChatQnA Docker Image Build

## Table of contents

1. [Build MegaService Docker Image](#Build-MegaService-Docker-Image)
2. [Build Basic UI Docker Image](#Build-Basic-UI-Docker-Image)
3. [Build Conversational React UI Docker Image](#Build-Conversational-React-UI-Docker-Image)
4. [Troubleshooting](#Troubleshooting)

## Build MegaService Docker Image

To construct the MegaService with Rerank, we utilize the [GenAIExamples](https://github.com/opea-project/GenAIExamples.git) microservice pipeline within the `chatqna.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
git fetch && git checkout tags/v1.2
cd GenAIExamples/ChatQnA
docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

## Build Basic UI Docker Image

Build the Frontend Docker Image using the command below:

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

## Build Conversational React UI Docker Image (Optional)

Build a frontend Docker image for an interactive conversational UI experience with ChatQnA MegaService

**Export the value of the public IP address of your host machine server to the `host_ip` environment variable**

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-conversation-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile.react .
```

## Troubleshooting

1. If you get errors like "Access Denied", [validate microservices](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/docker_compose/intel/cpu/xeon/README.md#validate-microservices) first. A simple example:

   ```bash
   http_proxy="" curl ${host_ip}:6006/embed -X POST  -d '{"inputs":"What is Deep Learning?"}' -H 'Content-Type: application/json'
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:8888, the port may be allocated by other users, you can modify the `compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.

## Monitoring OPEA Services with Prometheus and Grafana Dashboard

OPEA microservice deployment can easily be monitored through Grafana dashboards using data collected via Prometheus. Follow the [README](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/grafana/README.md) to setup Prometheus and Grafana servers and import dashboards to monitor the OPEA services.

![chatqna dashboards](./assets/img/chatqna_dashboards.png)
![tgi dashboard](./assets/img/tgi_dashboard.png)

## Tracing with OpenTelemetry and Jaeger

> NOTE: This feature is disabled by default. Please use the compose.telemetry.yaml file to enable this feature.

OPEA microservice and [TGI](https://huggingface.co/docs/text-generation-inference/en/index)/[TEI](https://huggingface.co/docs/text-embeddings-inference/en/index) serving can easily be traced through [Jaeger](https://www.jaegertracing.io/) dashboards in conjunction with [OpenTelemetry](https://opentelemetry.io/) Tracing feature. Follow the [README](https://github.com/opea-project/GenAIComps/tree/main/comps/cores/telemetry#tracing) to trace additional functions if needed.

Tracing data is exported to http://{EXTERNAL_IP}:4318/v1/traces via Jaeger.
Users could also get the external IP via below command.

```bash
ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+'
```

Access the Jaeger dashboard UI at http://{EXTERNAL_IP}:16686

For TGI serving on Gaudi, users could see different services like opea, TEI and TGI.
![Screenshot from 2024-12-27 11-58-18](https://github.com/user-attachments/assets/6126fa70-e830-4780-bd3f-83cb6eff064e)

Here is a screenshot for one tracing of TGI serving request.
![Screenshot from 2024-12-27 11-26-25](https://github.com/user-attachments/assets/3a7c51c6-f422-41eb-8e82-c3df52cd48b8)

There are also OPEA related tracings. Users could understand the time breakdown of each service request by looking into each opea:schedule operation.
![image](https://github.com/user-attachments/assets/6137068b-b374-4ff8-b345-993343c0c25f)

There could be asynchronous function such as `llm/MicroService_asyn_generate` and user needs to check the trace of the asynchronous function in another operation like
opea:llm_generate_stream.
![image](https://github.com/user-attachments/assets/a973d283-198f-4ce2-a7eb-58515b77503e)
