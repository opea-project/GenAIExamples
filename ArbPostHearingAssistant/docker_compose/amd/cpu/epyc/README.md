# Deploy Arbitration Post-Hearing Assistant Application on AMD EPYC™ Processors with Docker Compose

This document details the deployment procedure for a Arbitration Post-Hearing Assistant application using OPEA components on an AMD EPYC™ Processors.

This example includes the following sections:

- [Arbitration Post-Hearing Assistant Quick Start Deployment](#arb-post-hearing-assistant-quick-start-deployment): Demonstrates how to quickly deploy a Arbitration Post-Hearing Assistant application/pipeline on AMD EPYC platform.
- [Arbitration Post-Hearing Assistant Docker Compose Files](#arb-post-hearing-assistant-docker-compose-files): Describes some example deployments and their docker compose files.
- [Arbitration Post-Hearing Assistant Detailed Usage](#arb-post-hearing-assistant-detailed-usage): Provide more detailed usage.
- [Launch the UI](#launch-the-ui): Guideline for UI usage

## arb-post-hearing-assistant Quick Start Deployment

This section explains how to quickly deploy and manually test the Arbitration Post-Hearing Assistant service on an AMD EPYC platform. The process involves the following basic steps:

1. [Access the Code](#access-the-code)
2. [Install Docker](#install-docker)
3. [Determine your host external IP address](#determine-your-host-external-ip-address)
4. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
5. [Set Up Environment](#set-up-environment)
6. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
7. [Check the Deployment Status](#check-the-deployment-status)
8. [Test the Pipeline](#test-the-pipeline)
9. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the Arbitration Post-Hearing Assistant AMD EPYC platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ArbPostHearingAssistant/docker_compose/amd/cpu/epyc
```

### Install Docker

Ensure Docker is installed on your system. If Docker is not already installed, use the provided script to set it up:

    source ./install_docker.sh

This script installs Docker and its dependencies. After running it, verify the installation by checking the Docker version:

    docker --version

If Docker is already installed, this step can be skipped.

### Determine your host external IP address

Run the following command in your terminal to list network interfaces:

    ifconfig

Look for the inet address associated with your active network interface (e.g., enp99s0). For example:

    enp99s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.101.16.119  netmask 255.255.255.0  broadcast 10.101.16.255

In this example, the (`host_ip`) would be (`10.101.16.119`).

    # Replace with your host's external IP address
    export host_ip="your_external_ip_address"

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

```bash
export HF_TOKEN="your_huggingface_token"
```

### Set Up Environment

Set the environment variables

```bash
source ./set_env.sh
```

NOTE: by default vLLM does "warmup" at start, to optimize its performance for the specified model and the underlying platform, which can take long time. For development (and e.g. autoscaling) it can be skipped with `export VLLM_SKIP_WARMUP=true`.

### Deploy the Services Using Docker Compose

To deploy the Arbitration Post-Hearing Assistant services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

**Note**: developers should build docker image from source when:

- Developing off the git main branch (as the container's ports in the repo may be different from the published docker image).
- Unable to download the docker image.
- Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice                   | Deployment Guide                                                                                                                                            |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| vLLM                           | [vLLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/vllm#build-docker)                                              |
| llm-arb-post-hearing-assistant | [LLM-ArbPostHearingAssistant build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/arb_post_hearing_assistant/src/#12-build-docker-image) |
| MegaService                    | [MegaService build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image)                                                               |
| UI                             | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                                                                           |

### Check the Deployment Status

After running docker compose, to check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment, the following 4 containers should be running:

```bash
CONTAINER ID   IMAGE                                                           COMMAND                  CREATED       STATUS                 PORTS                                         NAMES
24bd78300413   opea/arb-post-hearing-assistant-gradio-ui:latest                "python arb_post_hea…"   2 hours ago   Up 2 hours             0.0.0.0:5173->5173/tcp, [::]:5173->5173/tcp   arb-post-hearing-assistant-xeon-ui-server
59e60c954e26   opea/arb-post-hearing-assistant:latest                          "python arb_post_hea…"   2 hours ago   Up 2 hours             0.0.0.0:8888->8888/tcp, [::]:8888->8888/tcp   arb-post-hearing-assistant-xeon-backend-server
32afc12de996   opea/llm-arb-post-hearing-assistant:latest                      "python comps/arb_po…"   2 hours ago   Up 2 hours             0.0.0.0:9000->9000/tcp, [::]:9000->9000/tcp   arb-post-hearing-assistant-xeon-llm-server
c8e539360aff   ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu   "text-generation-lau…"   2 hours ago   Up 2 hours (healthy)   0.0.0.0:8008->80/tcp, [::]:8008->80/tcp       arb-post-hearing-assistant-xeon-tgi-server
```

### Test the Pipeline

Once the Arbitration Post-Hearing Assistant services are running, test the pipeline using the following command:

```bash
curl -X POST http://${host_ip}:8888/v1/arb-post-hearing \
        -H "Content-Type: application/json" \
        -d '{"type": "text", [10:00 AM] Arbitrator Hon. Rebecca Lawson: Good morning. This hearing is now in session for Case No. ARB/2025/0917. Lets begin with appearances. [10:01 AM] Attorney Michael Grant for Mr. Jonathan Reed: Good morning Your Honor. I represent the claimant Mr. Jonathan Reed. [10:01 AM] Attorney Lisa Chen for Ms. Rachel Morgan: Good morning. I represent the respondent Ms. Rachel Morgan. [10:03 AM] Arbitrator Hon. Rebecca Lawson: Thank you. Lets proceed with Mr. Reeds opening statement. [10:04 AM] Attorney Michael Grant: Ms. Morgan failed to deliver services as per the agreement dated March 15 2023. We have submitted relevant documentation including email correspondence and payment records. The delay caused substantial financial harm to our client. [10:15 AM] Attorney Lisa Chen: We deny any breach of contract. The delays were due to regulatory issues outside our control. Furthermore Mr. Reed did not provide timely approvals which contributed to the delay. [10:30 AM] Arbitrator Hon. Rebecca Lawson: Lets turn to Clause Z of the agreement. Id like both parties to submit written briefs addressing the applicability of the force majeure clause and the timeline of approvals. [11:00 AM] Attorney Michael Grant: Understood. Well submit by the deadline. [11:01 AM] Attorney Lisa Chen: Agreed. [11:02 AM] Arbitrator Hon. Rebecca Lawson: The next hearing is scheduled for October 22 2025 at 1030 AM Eastern Time. Please ensure your witnesses are available for cross examination. [4:45 PM] Arbitrator Hon. Rebecca Lawson: This session is adjourned. Thank you everyone.","max_tokens":2000,"language":"en"}'
```

**Note** The value of _host_ip_ was set using the _set_env.sh_ script and can be found in the _.env_ file.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```

All the Arbitration Post-Hearing Assistant containers will be stopped and then removed on completion of the "down" command.

## arb-post-hearing-assistant Docker Compose Files

In the context of deploying a Arbitration Post-Hearing Assistant pipeline on an AMD EPYC platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application.

| File                                   | Description                                                                               |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)         | Default compose file using vllm as serving framework                                      |
| [compose_tgi.yaml](./compose_tgi.yaml) | The LLM serving framework is TGI. All other configurations remain the same as the default |

## arb-post-hearing-assistant Assistant Detailed Usage

There are also some customized usage.

### Query with text

```bash
# form input. Use English mode (default).
curl http://${host_ip}:8888/v1/arb-post-hearing \
      -H "Content-Type: multipart/form-data" \
      -F "type=text" \
      -F "messages=[10:00 AM] Arbitrator Hon. Rebecca Lawson: Good morning. This hearing is now in session for Case No. ARB/2025/0917. Lets begin with appearances. [10:01 AM] Attorney Michael Grant for Mr. Jonathan Reed: Good morning Your Honor. I represent the claimant Mr. Jonathan Reed. [10:01 AM] Attorney Lisa Chen for Ms. Rachel Morgan: Good morning. I represent the respondent Ms. Rachel Morgan. [10:03 AM] Arbitrator Hon. Rebecca Lawson: Thank you. Lets proceed with Mr. Reeds opening statement. [10:04 AM] Attorney Michael Grant: Ms. Morgan failed to deliver services as per the agreement dated March 15 2023. We have submitted relevant documentation including email correspondence and payment records. The delay caused substantial financial harm to our client. [10:15 AM] Attorney Lisa Chen: We deny any breach of contract. The delays were due to regulatory issues outside our control. Furthermore Mr. Reed did not provide timely approvals which contributed to the delay. [10:30 AM] Arbitrator Hon. Rebecca Lawson: Lets turn to Clause Z of the agreement. Id like both parties to submit written briefs addressing the applicability of the force majeure clause and the timeline of approvals. [11:00 AM] Attorney Michael Grant: Understood. Well submit by the deadline. [11:01 AM] Attorney Lisa Chen: Agreed. [11:02 AM] Arbitrator Hon. Rebecca Lawson: The next hearing is scheduled for October 22 2025 at 1030 AM Eastern Time. Please ensure your witnesses are available for cross examination. [4:45 PM] Arbitrator Hon. Rebecca Lawson: This session is adjourned. Thank you everyone." \
      -F "max_tokens=2000" \
      -F "language=en"

## Launch the UI

### Gradio UI

Open this URL `http://{host_ip}:5173` in your browser to access the Gradio based frontend.
![project-screenshot](../../../../assets/img/arbritation_post_hearing_ui_gradio_text.png)

### Profile Microservices

To further analyze MicroService Performance, users could follow the instructions to profile MicroServices.

#### 1. vLLM backend Service

Users could follow previous section to testing vLLM microservice or Arbitration Post-Hearing Assistant MegaService. By default, vLLM profiling is not enabled. Users could start and stop profiling by following commands.

## Conclusion

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
```
