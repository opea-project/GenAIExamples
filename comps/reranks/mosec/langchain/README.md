# Reranking Microservice with Mosec

`Mosec` is a high-performance and flexible model serving framework for building ML model-enabled backend and microservices.

Please refer to [Official mosec repo](https://github.com/mosecorg/mosec)
for more information.

This README provides set-up instructions and comprehensive details regarding the reranking microservice via mosec.

---

## Build Reranking Mosec Image

- Build reranking mosec endpoint docker image.

  ```
  docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/reranking-langchain-mosec-endpoint:latest -f comps/reranks/mosec/langchain/dependency/Dockerfile .
  ```

---

## Build Reranking Microservice Image

- Build reranking microservice docker image.

  ```
  docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/reranking-langchain-mosec:latest -f comps/reranks/mosec/langchain/Dockerfile .
  ```

---

## Launch Mosec Endpoint Image Container

- Start the mosec endpoint image docker container.

  ```
  docker run -d --name="reranking-langchain-mosec-endpoint" -p 6001:8000  opea/reranking-langchain-mosec-endpoint:latest
  ```

---

## Launch Embedding Microservice Image Container

- Start the embedding microservice image docker container.

  ```
  export MOSEC_RERANKING_ENDPOINT=http://127.0.0.1:6001

  docker run -d --name="reranking-langchain-mosec-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 6000:8000 --ipc=host -e MOSEC_RERANKING_ENDPOINT=$MOSEC_RERANKING_ENDPOINT opea/reranking-langchain-mosec:latest
  ```

---

## ✅ Invoke Reranking Microservice

The Reranking microservice exposes following API endpoints:

- Execute reranking process by providing query and documents

  ```
  curl http://localhost:6000/v1/reranking \
     -X POST \
     -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
     -H 'Content-Type: application/json'
  ```
