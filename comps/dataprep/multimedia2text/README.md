# Multimedia to Text Services

This guide provides instructions on how to build and run various Docker services for converting multimedia content to text. The services include:

1. **Whisper Service**: Converts audio to text.
2. **A2T Service**: Another service for audio to text conversion.
3. **Video to Audio Service**: Extracts audio from video files.
4. **Multimedia2Text Service**: Transforms multimedia data to text data.

## Prerequisites

1. **Docker**: Ensure you have Docker installed and running on your system. You can download and install Docker from the [official Docker website](https://www.docker.com/get-started).

2. **Proxy Settings**: If you are behind a corporate firewall, make sure you have the necessary proxy settings configured. This will ensure that Docker and other tools can access the internet.

3. **Python**: If you want to validate services using the provided Python scripts, ensure you have Python 3.11 installed. The current validation tests have been tested with Python 3.11. You can check your Python version by running the following command in your terminal:
   ```bash
   python --version
   ```

## Getting Started

First, navigate to the `GenAIComps` directory:

```bash
cd GenAIComps
```

### Whisper Service

The Whisper Service converts audio files to text. Follow these steps to build and run the service:

#### Build

```bash
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/dependency/Dockerfile .
```

#### Run

```bash
docker run -d -p 7066:7066 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/whisper:latest
```

### A2T Service

The A2T Service is another service for converting audio to text. Follow these steps to build and run the service:

#### Build

```bash
docker build -t opea/a2t:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimedia2text/audio2text/Dockerfile .
```

#### Run

```bash
host_ip=$(hostname -I | awk '{print $1}')

docker run -d -p 9099:9099 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e A2T_ENDPOINT=http://$host_ip:7066 opea/a2t:latest
```

### Video to Audio Service

The Video to Audio Service extracts audio from video files. Follow these steps to build and run the service:

#### Build

```bash
docker build -t opea/v2a:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimedia2text/video2audio/Dockerfile .
```

#### Run

```bash
docker run -d -p 7078:7078 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/v2a:latest
```

### Multimedia2Text Service

The Multimedia2Text Service transforms multimedia data to text data. Follow these steps to build and run the service:

#### Build

```bash
docker build -t opea/multimedia2text:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimedia2text/Dockerfile .
```

#### Run

```bash
host_ip=$(hostname -I | awk '{print $1}')

docker run -d -p 7079:7079 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy \
    -e A2T_ENDPOINT=http://$host_ip:7066 \
    -e V2A_ENDPOINT=http://$host_ip:7078 \
    opea/multimedia2text:latest
```

## Validate Microservices

After building and running the services, you can validate them using the provided Python scripts. Below are the steps to validate each service:

### Whisper Service

Run the following command to validate the Whisper Service:

```bash
python comps/asr/whisper/dependency/check_whisper_server.py
```

Expected output:

```
{'asr_result': 'who is pat gelsinger'}
```

### Audio2Text Service

Run the following command to validate the Audio2Text Service:

```bash
python comps/dataprep/multimedia2text/audio2text/check_a2t_server.py
```

Expected output:

```
Test passed successfully!
```

_Note: The `id` value will be different._

### Video2Audio Service

Run the following command to validate the Video2Audio Service:

```bash
python comps/dataprep/multimedia2text/video2audio/check_v2a_microserver.py
```

Expected output:

```
========= Audio file saved as ======
comps/dataprep/multimedia2text/video2audio/converted_audio.wav
====================================
```

### Multimedia2Text Service

Run the following command to validate the Multimedia2Text Service:

```bash
python comps/dataprep/multimedia2text/check_multimedia2text.py
```

Expected output:

```
Running test: Whisper service
>>> Whisper service Test Passed ...

Running test: Audio2Text service
>>> Audio2Text service Test Passed ...

Running test: Video2Text service
>>> Video2Text service Test Passed ...

Running test: Multimedia2text service
>>> Multimedia2text service test for text data type passed ...
>>> Multimedia2text service test for audio data type passed ...
>>> Multimedia2text service test for video data type passed ...
```

## How to Stop/Remove Services

To stop and remove the Docker containers and images associated with the multimedia-to-text services, follow these steps:

1. **List Running Containers**: First, list all running Docker containers to identify the ones you want to stop and remove.

   ```bash
   docker ps
   ```

2. **Stop Containers**: Use the `docker stop` command followed by the container IDs or names to stop the running containers.

   ```bash
   docker stop <container_id_or_name>
   ```

   If you want to stop all running containers at once, you can use:

   ```bash
   docker stop $(docker ps -q)
   ```

3. **Remove Containers**: After stopping the containers, use the `docker rm` command followed by the container IDs or names to remove them.

   ```bash
   docker rm <container_id_or_name>
   ```

   Optionally, you can remove the stopped containers to free up resources:

   ```bash
   docker rm $(docker ps -a -q)
   ```

4. **Remove Images**: If you also want to remove the Docker images, use the `docker rmi` command followed by the image IDs or names.

   ```bash
   docker rmi <image_id_or_name>
   ```

   To remove all unused images, you can use:

   ```bash
   docker image prune -a
   ```
