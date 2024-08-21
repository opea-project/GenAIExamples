# LVM Microservice

This is a Docker-based microservice that runs Video-Llama as a Large Vision Model (LVM). It utilizes Llama-2-7b-chat-hf for conversations based on video dialogues. It support Intel Xeon CPU.

# 🚀1. Start Microservice with Docker

## 1.1 Build Images

```bash
cd GenAIComps
# Video-Llama Server Image
docker build --no-cache -t opea/video-llama-lvm-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/video-llama/server/docker/Dockerfile .
# LVM Service Image
docker build --no-cache -t opea/lvm-video-llama:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/lvms/video-llama/Dockerfile .
```

## 1.2 Start Video-Llama and LVM Services

For the very first run, please follow below steps:

```bash
# prepare environment variables
export ip_address=$(hostname -I | awk '{print $1}')
export no_proxy=$no_proxy,${ip_address}
export LVM_ENDPOINT=http://${ip_address}:9009
# Start service
docker compose -f comps/lvms/video-llama/docker_compose.yaml up -d
# it should take about 1.5 hours for the model to download in the video-llama server, assuming a maximum download speed of 100 Mbps
until docker logs video-llama-lvm-server 2>&1 | grep -q "Uvicorn running on"; do
    sleep 5m
done
```

If you've run the microservice before, it's recommended to keep the downloaded model so it won't be redownloaded each time you run it. To achieve this, you need to modify the following configuration:

```yaml
# comps/lvms/video-llama/docker_compose.yaml
services:
  lvm-video-llama:
    ...
    environment:
      llm_download: "False" # avoid download
```

# ✅ 2. Test

```bash
# use curl
export ip_address=$(hostname -I | awk '{print $1}')
## check video-llama
http_proxy="" curl -X POST "http://${ip_address}:9009/generate?video_url=https%3A%2F%2Fgithub.com%2FDAMO-NLP-SG%2FVideo-LLaMA%2Fraw%2Fmain%2Fexamples%2Fsilence_girl.mp4&start=0.0&duration=9&prompt=What%20is%20the%20person%20doing%3F&max_new_tokens=150" -H "accept: */*" -d ''

## check lvm
http_proxy="" curl -X POST http://${ip_address}:9000/v1/lvm -d '{"video_url":"https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4","chunk_start": 0,"chunk_duration": 9,"prompt":"What is the person doing?","max_new_tokens": 150}' -H 'Content-Type: application/json'

# or use python
export ip_address=$(hostname -I | awk '{print $1}')
python comps/lvms/video-llama/check_lvm.py
```

# ♻️ 3. Clean

```bash
# remove the container
cid=$(docker ps -aq --filter "name=video-llama")
if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
# remove the model volume (suggest to keep this to avoid download for each run)
if docker volume ls | grep -q video-llama-model; then docker volume rm video-llama_video-llama-model; fi

```
