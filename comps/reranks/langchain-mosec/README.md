# build reranking Mosec endpoint docker image

```
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/reranking-langchain-mosec-endpoint:latest -f comps/reranks/langchain-mosec/mosec-docker/Dockerfile .
```

# build reranking microservice docker image

```
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/reranking-langchain-mosec:latest -f comps/reranks/langchain-mosec/docker/Dockerfile .
```

# launch Mosec endpoint docker container

```
docker run -d --name="reranking-langchain-mosec-endpoint" -p 6001:8000  opea/reranking-langchain-mosec-endpoint:latest
```

# launch embedding microservice docker container

```
export MOSEC_RERANKING_ENDPOINT=http://127.0.0.1:6001
docker run -d --name="reranking-langchain-mosec-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 6000:8000 --ipc=host -e MOSEC_RERANKING_ENDPOINT=$MOSEC_RERANKING_ENDPOINT opea/reranking-langchain-mosec:latest
```

# run client test

```
curl http://localhost:6000/v1/reranking \
   -X POST \
   -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
   -H 'Content-Type: application/json'
```
