# Arbitration Post-Hearing Assistant

The Arbitration Post-Hearing Assistant is a GenAI-based module designed to process and summarize post-hearing transcripts or arbitration-related documents. It intelligently extracts key entities and insights to assist arbitrators, legal teams, and case managers in managing case follow-ups efficiently.

## Key Features

Automated Information Extraction:
Identifies and extracts essential details such as:

- Case number
- Parties involved (claimant/respondent)
- Arbitrator(s)
- Hearing date and time
- Next hearing schedule and purpose
- Hearing outcomes and reasons

## Docker

### Build UI Docker Image

To build the frontend Docker image, navigate to the `GenAIExamples/ArbPostHearingAssistant/ui` directory and run the following command:

```bash
cd GenAIExamples/ArbPostHearingAssistant/ui
docker build -t opea/arb-post-hearing-assistant-gradio-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile.gradio .
```

This command builds the Docker image with the tag `opea/arb-post-hearing-assistant-gradio-ui:latest`. It also passes the proxy settings as build arguments to ensure that the build process can access the internet if you are behind a corporate firewall.

### Run UI Docker Image

To run the frontend Docker image, navigate to the `GenAIExamples/ArbPostHearingAssistant/ui/docker` directory and execute the following commands:

```bash
cd GenAIExamples/ArbPostHearingAssistant/ui/docker

ip_address=$(hostname -I | awk '{print $1}')
docker run -d -p 5173:5173 --ipc=host \
   -e http_proxy=$http_proxy \
   -e https_proxy=$https_proxy \
   -e no_proxy=$no_proxy \
   -e BACKEND_SERVICE_ENDPOINT=http://localhost:8888/v1/docsum \
   opea/arb-post-hearing-assistant-gradio-ui:latest
```

This command runs the Docker container in interactive mode, mapping port 5173 of the host to port 5173 of the container. It also sets several environment variables, including the backend service endpoint, which is required for the frontend to communicate with the backend service.

### Python

To run the frontend application directly using Python, navigate to the `GenAIExamples/ArbPostHearingAssistant/ui/gradio` directory and run the following command:

```bash
cd GenAIExamples/ArbPostHearingAssistant/ui/gradio
python arb_post_hearing_assistant_ui_gradio.py
```

This command starts the frontend application using Python.

## 📸 Project Screenshots

![project-screenshot](../../assets/img/arbritation_post_hearing_ui_gradio_text.png)

### 🧐 Features

Here are some of the project's features:

## Features

- **Automated Case Extraction:** Extracts key arbitration details including case number, claimant/respondent, arbitrator, hearing dates, next hearing schedule, and outcome.
- **Hearing Summarization:** Generates concise summaries of post-hearing proceedings.
- **LLM-Powered Processing:** Integrates with vLLM or TGI backends for natural language understanding.
- **Structured Output:** Returns all extracted information in JSON format for easy storage, display, or integration with case management systems.
- **Easy Deployment:** Containerized microservice, lightweight and reusable across legal workflows.
- **Typical Flow:**
  1. Upload or stream post-hearing transcript.
  2. LLM backend analyzes text and extracts entities.
  3. Returns structured JSON with case details and summary.

## Additional Information

### Prerequisites

Ensure you have Docker installed and running on your system. Also, make sure you have the necessary proxy settings configured if you are behind a corporate firewall.

### Environment Variables

- `http_proxy`: Proxy setting for HTTP connections.
- `https_proxy`: Proxy setting for HTTPS connections.
- `no_proxy`: Comma-separated list of hosts that should be excluded from proxying.
- `BACKEND_SERVICE_ENDPOINT`: The endpoint of the backend service that the frontend will communicate with.

### Troubleshooting

- Docker Build Issues: If you encounter issues while building the Docker image, ensure that your proxy settings are correctly configured and that you have internet access.
- Docker Run Issues: If the Docker container fails to start, check the environment variables and ensure that the backend service is running and accessible.

This README file provides detailed instructions and explanations for building and running the Dockerized frontend application, as well as running it directly using Python. It also highlights the key features of the project and provides additional information for troubleshooting and configuring the environment.
