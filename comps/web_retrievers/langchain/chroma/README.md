# Web Retriever Microservice

The Web Retriever Microservice is designed to efficiently search web pages relevant to the prompt, save them into the VectorDB, and retrieve the matched documents with the highest similarity. The retrieved documents will be used as context in the prompt to LLMs. Different from the normal RAG process, a web retriever can leverage advanced search engines for more diverse demands, such as real-time news, verifiable sources, and diverse sources.

# Start Microservice with Docker

## Build Docker Image

```bash
cd ../../
docker build -t opea/web-retriever-chroma:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/web_retrievers/langchain/chroma/docker/Dockerfile .
```

## Start TEI Service

```bash
model=BAAI/bge-base-en-v1.5
revision=refs/pr/4
volume=$PWD/data
docker run -d -p 6060:80 -v $volume:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model --revision $revision
```

## Start Web Retriever Service

```bash
# set TEI endpoint
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"

# set search engine env variables
export GOOGLE_API_KEY=xxx
export GOOGLE_CSE_ID=xxx
```

```bash
docker run -d --name="web-retriever-chroma-server" -p 7078:7077 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT opea/web-retriever-chroma:latest
```

## Consume Web Retriever Service

To consume the Web Retriever Microservice, you can generate a mock embedding vector of length 768 with Python.

```bash
# Test
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

curl http://${your_ip}:7077/v1/web_retrieval \
  -X POST \
  -d "{\"text\":\"What is OPEA?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```
