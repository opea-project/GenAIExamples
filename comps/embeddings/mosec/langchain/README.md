# build Mosec endpoint docker image

```
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/embedding-langchain-mosec-endpoint:latest -f comps/embeddings/mosec/langchain/dependency/Dockerfile .
```

## build embedding microservice docker image

```
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/embedding-langchain-mosec:latest -f comps/embeddings/mosec/langchain/Dockerfile .
```

## launch Mosec endpoint docker container

```
docker run -d --name="embedding-langchain-mosec-endpoint" -p 6001:8000  opea/embedding-langchain-mosec-endpoint:latest
```

## launch embedding microservice docker container

```
export MOSEC_EMBEDDING_ENDPOINT=http://{mosec_embedding_host_ip}:6001
docker run -d --name="embedding-langchain-mosec-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 6000:6000 --ipc=host -e MOSEC_EMBEDDING_ENDPOINT=$MOSEC_EMBEDDING_ENDPOINT opea/embedding-langchain-mosec:latest
```

## run client test

```
curl localhost:6000/v1/embeddings \
     -X POST \
     -d '{"text":"Hello, world!"}' \
     -H 'Content-Type: application/json'
```
