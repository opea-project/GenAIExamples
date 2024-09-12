# Rerank Microservice

This is a Docker-based microservice that do result rerank for VideoQnA use case. Local rerank is used rather than rerank model.

For the `VideoQnA` usecase, during the data preparation phase, frames are extracted from videos and stored in a vector database. To identify the most relevant video, we count the occurrences of each video source among the retrieved data with rerank function `get_top_doc`. This sorts the video as a descending list of names, ranked by their degree of match with the query. Then we could send the `top_n` videos to the downstream LVM.

## 🚀1. Start Microservice with Docker

### 1.1 Build Images

```bash
cd GenAIComps
docker build --no-cache -t opea/reranking-videoqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/reranks/videoqna/Dockerfile .
```

### 1.2 Start Rerank Service

```bash
docker compose -f comps/reranks/videoqna/docker_compose_reranking.yaml up -d
# wait until ready
until docker logs reranking-videoqna-server 2>&1 | grep -q "Uvicorn running on"; do
    sleep 2
done
```

Available configuration by environment variable:

- CHUNK_DURATION: target chunk duration, should be aligned with VideoQnA dataprep. Default 10s.

## ✅ 2. Test

```bash
export ip_address=$(hostname -I | awk '{print $1}')
curl -X 'POST' \
"http://${ip_address}:8000/v1/reranking" \
-H 'accept: application/json' \
-H 'Content-Type: application/json' \
-d '{
  "retrieved_docs": [{"doc": [{"text": "this is the retrieved text"}]}],
  "initial_query": "this is the query",
  "top_n": 1,
  "metadata": [
      {"other_key": "value", "video":"top_video_name", "timestamp":"20"},
      {"other_key": "value", "video":"second_video_name", "timestamp":"40"},
      {"other_key": "value", "video":"top_video_name", "timestamp":"20"}
  ]
}'
```

The result should be:

```bash
{"id":"random number","video_url":"http://0.0.0.0:6005/top_video_name","chunk_start":20.0,"chunk_duration":10.0,"prompt":"this is the query","max_new_tokens":512}
```

## ♻️ 3. Clean

```bash
# remove the container
cid=$(docker ps -aq --filter "name=reranking-videoqna-server")
if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
```
