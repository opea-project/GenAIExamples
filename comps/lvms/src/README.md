# LVM Microservice

Visual Question and Answering is one of the multimodal tasks empowered by LVMs (Large Visual Models). This microservice supports visual Q&A by using LLaVA as the base large visual model. It accepts two inputs: a prompt and an image. It outputs the answer to the prompt about the image.

## Build Image & Run

Before this, you have to start the [dependency](./integrations/dependency/) service based on your demands.

```bash
docker build --no-cache -t opea/lvm:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/lvms/src/Dockerfile .
# Change LVM_ENDPOINT to you dependency service endpoint
docker run -d --name="test-comps-lvm" -e LVM_ENDPOINT=http://localhost:8399 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9399:9399 --ipc=host opea/lvm:comps
```

## Test

- LLaVA & llama-vision & PredictionGuard & TGI LLaVA

```bash
# curl with an image and a prompt
http_proxy="" curl http://localhost:9399/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}' -H 'Content-Type: application/json'

# curl with only the prompt
http_proxy="" curl http://localhost:9399/v1/lvm --silent --write-out "HTTPSTATUS:%{http_code}" -XPOST -d '{"image": "", "prompt":"What is deep learning?"}' -H 'Content-Type: application/json'
```

- video-llama

```bash
http_proxy="" curl -X POST http://localhost:9399/v1/lvm -d '{"video_url":"https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4","chunk_start": 0,"chunk_duration": 9,"prompt":"What is the person doing?","max_new_tokens": 150}' -H 'Content-Type: application/json'
```
