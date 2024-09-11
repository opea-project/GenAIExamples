# Retriever Microservice with Pathway

## 🚀Start Microservices

### With the Docker CLI

We suggest using `docker compose` to run this app, refer to [`docker compose`](#with-the-docker-compose) section below.

If you prefer to run them separately, refer to this section.

#### (Optionally) Start the TEI (embedder) service separately

> Note that Docker compose will start this service as well, this step is thus optional.

```bash
model=BAAI/bge-base-en-v1.5
# TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"  # if you want to use the hosted embedding service, example: "http://127.0.0.1:6060"

# then run:
docker run -p 6060:80 -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
```

Health check the embedding service with:

```bash
curl 127.0.0.1:6060/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

If the model supports re-ranking, you can also use:

```bash
curl 127.0.0.1:6060/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

#### Start Retriever Service

Retriever service queries the Pathway vector store on incoming requests.
Make sure that Pathway vector store is already running, [see Pathway vector store here](../../../vectorstores/pathway/README.md).

Retriever service expects the Pathway host and port variables to connect to the vector DB. Set the Pathway vector store environment variables.

```bash
export PATHWAY_HOST=0.0.0.0
export PATHWAY_PORT=8666
```

```bash
# make sure you are in the root folder of the repo
docker build -t opea/retriever-pathway:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/pathway/langchain/Dockerfile .

docker run -p 7000:7000 -e PATHWAY_HOST=${PATHWAY_HOST} -e PATHWAY_PORT=${PATHWAY_PORT} -e http_proxy=$http_proxy -e https_proxy=$https_proxy --network="host" opea/retriever-pathway:latest
```

### With the Docker compose

First, set the env variables:

```bash
export PATHWAY_HOST=0.0.0.0
export PATHWAY_PORT=8666
model=BAAI/bge-base-en-v1.5
# TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"  # if you want to use the hosted embedding service, example: "http://127.0.0.1:6060"
```

Text embeddings inference service expects the `RETRIEVE_MODEL_ID` variable to be set.

```bash
export RETRIEVE_MODEL_ID=BAAI/bge-base-en-v1.5
```

Note that following docker compose sets the `network_mode: host` in retriever image to allow local vector store connection.
This will start the both the embedding and retriever services:

```bash
cd comps/retrievers/pathway/langchain

docker compose -f docker_compose_retriever.yaml build
docker compose -f docker_compose_retriever.yaml up

# shut down the containers
docker compose -f docker_compose_retriever.yaml down
```

Make sure the retriever service is working as expected:

```bash
curl http://0.0.0.0:7000/v1/health_check   -X GET   -H 'Content-Type: application/json'
```

send an example query:

```bash
exm_embeddings=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

curl http://0.0.0.0:7000/v1/retrieval   -X POST   -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${exm_embeddings}}"   -H 'Content-Type: application/json'
```
