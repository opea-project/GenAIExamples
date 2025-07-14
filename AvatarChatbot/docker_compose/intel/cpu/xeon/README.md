# Example AvatarChatbot Deployment on Intel® Xeon® Platform

This document outlines the deployment process for a AvatarChatbot application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. This example includes the following sections:

- [AvatarChatbot Quick Start Deployment](#avatarchatbot-quick-start-deployment): Demonstrates how to quickly deploy a AvatarChatbot service/pipeline on Intel Xeon server.
- [AvatarChatbot Docker Compose Files](#avatarchatbot-docker-compose-files): Describes some example deployments and their docker compose files.
- [AvatarChatbot Service Configuration](#avatarchatbot-service-configuration): Describes the service and possible configuration changes.

## AvatarChatbot Quick Start Deployment

This section describes how to quickly deploy and test the AvatarChatbot service manually on Intel Xeon server. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
3. [Configure the Deployment Environment](#configure-the-deployment-environment)
4. [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
5. [Check the Deployment Status](#check-the-deployment-status)
6. [Test the Pipeline](#test-the-pipeline)
7. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExamples repository and access the AvatarChatbot Intel Xeon server Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AvatarChatbot/docker_compose/intel/cpu/xeon/
```

Checkout a released version, such as v1.3:

```
git checkout v1.3
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying AvatarChatbot service, source the _set_env.sh_ script in this directory:

```
source set_env.sh
```

The set_env.sh script will prompt for required and optional environment variables used to configure the AvatarChatbot service. If a value is not entered, the script will use a default value for the same. It will also generate a env file defining the desired configuration. Consult the section on [AvatarChatbot Service configuration](#avatarchatbot-service-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Service Using Docker Compose

To deploy the AvatarChatbot service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The AvatarChatbot docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel Xeon server:

```
[+] Running 7/7
 ✔ Network xeon_default                         Created                                                                                                         0.1s
 ✔ Container whisper-service                    Started                                                                                                         4.4s
 ✔ Container speecht5-service                   Started                                                                                                         4.7s
 ✔ Container wav2lip-service                    Started                                                                                                         4.7s
 ✔ Container animation-server                   Started                                                                                                         4.1s
 ✔ Container tgi-service                        Started                                                                                                         4.7s
 ✔ Container avatarchatbot-xeon-backend-server  Started                                                                                                         1.0s
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running:

```
CONTAINER ID   IMAGE                                                           COMMAND                  CREATED          STATUS                                  PORTS                                         NAMES
706f3ae2c4eb   opea/avatarchatbot:latest                                       "python avatarchatbo…"   16 seconds ago   Up 15 seconds                                                 avatarchatbot-xeon-backend-server
5dfa217b5376   opea/animation:latest                                           "python3 opea_animat…"   16 seconds ago   Up 15 seconds                           0.0.0.0:3008->9066/tcp, :::3008->9066/tcp     animation-server
60b69f113f24   ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu   "text-generation-lau…"   16 seconds ago   Up 15 seconds                                                             tgi-service
518b409b59c2   opea/speecht5:latest                                            "python speecht5_ser…"   16 seconds ago   Up 16 seconds                           0.0.0.0:7055->7055/tcp, :::7055->7055/tcp     speecht5-service
6454bf20eb5f   opea/wav2lip:latest                                             "/usr/local/bin/entr…"   16 seconds ago   Up 2 seconds                            0.0.0.0:7860->7860/tcp, :::7860->7860/tcp     wav2lip-service
eb751a90f76a   opea/whisper:latest                                             "python whisper_serv…"   16 seconds ago   Up 15 seconds                           0.0.0.0:7066->7066/tcp, :::7066->7066/tcp     whisper-service
```

### Test the Pipeline

Once the AvatarChatbot service are running, test the pipeline using the following command:

```bash
curl http://${host_ip}:3009/v1/avatarchatbot \
  -X POST \
  -d @assets/audio/sample_whoareyou.json \
  -H 'Content-Type: application/json'
```

If the megaservice is running properly, you should see the following output:

```bash
"/outputs/result.mp4"
```

The output file will be saved in the current working directory, as `${PWD}` is mapped to `/outputs` inside the wav2lip-service Docker container.

**Note** The value of _host_ip_ was set using the _set_env.sh_ script and can be found in the _.env_ file.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

```
[+] Running 7/7
 ✔ Container wav2lip-service                    Removed                                                                                                        10.9s
 ✔ Container speecht5-service                   Removed                                                                                                         3.4s
 ✔ Container whisper-service                    Removed                                                                                                         2.9s
 ✔ Container avatarchatbot-xeon-backend-server  Removed                                                                                                        10.7s
 ✔ Container tgi-service                        Removed                                                                                                         3.5s
 ✔ Container animation-server                   Removed                                                                                                        11.1s
 ✔ Network xeon_default                         Removed                                                                                                         2.1s
```

All the AvatarChatbot containers will be stopped and then removed on completion of the "down" command.

## AvatarChatbot Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name                      | Image Name                                                    |
| --------------------------------- | ------------------------------------------------------------- |
| tgi-service                       | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu |
| whisper-service                   | opea/whisper:latest                                           |
| speecht5-service                  | opea/speecht5:latest                                          |
| wav2lip-service                   | opea/wav2lip:latest                                           |
| animation                         | opea/animation:latest                                         |
| avatarchatbot-xeon-backend-server | opea/avatarchatbot:latest                                     |

## AvatarChatbot Service Configuration

The table provides a comprehensive overview of the AvatarChatbot service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name                      | Possible Image Names                                          | Optional | Description                                                                                      |
| --------------------------------- | ------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------ |
| tgi-service                       | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu | No       | Specific to the TGI deployment, focuses on text generation inference using Xeon hardware.        |
| whisper-service                   | opea/whisper:latest                                           | No       | Provides automatic speech recognition (ASR), converting spoken audio input into text.            |
| speecht5-service                  | opea/speecht5:latest                                          | No       | Performs text-to-speech (TTS) synthesis, generating natural-sounding speech from text.           |
| wav2lip-service                   | opea/wav2lip:latest                                           | No       | Generates realistic lip-sync animations by aligning speech audio with a video of a face.         |
| animation                         | opea/animation:latest                                         | No       | Handles avatar animation, rendering facial expressions and movements for the chatbot avatar.     |
| avatarchatbot-xeon-backend-server | opea/avatarchatbot:latest                                     | No       | Orchestrates the overall AvatarChatbot pipeline, managing requests and integrating all services. |
