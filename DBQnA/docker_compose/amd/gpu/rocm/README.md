# Deploy on AMD GPU

This document outlines the deployment process for DBQnA application which helps generating a SQL query and its output given a NLP question, utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on an AMD GPU. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices. We will publish the Docker images to Docker Hub soon, which will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored once the Docker images are published to Docker hub.

### 1.1 Build Text to SQL service Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build --no-cache -t opea/texttosql:latest -f comps/text2sql/src/Dockerfile .
```

### 1.2 Build react UI Docker Image

Build the frontend Docker image based on react framework via below command:

```bash
cd GenAIExamples/DBQnA/ui
docker build --no-cache -t opea/dbqna-react-ui:latest --build-arg texttosql_url=$textToSql_host:$textToSql_port/v1 -f docker/Dockerfile.react .
```

Attention! Replace $textToSql_host and $textToSql_port with your own value.

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/texttosql:latest`
2. `opea/dbqna-react-ui:latest`

## 🚀 Start Microservices

### Required Models

We set default model as "mistralai/Mistral-7B-Instruct-v0.3", change "LLM_MODEL_ID" in following Environment Variables setting if you want to use other models.

If use gated models, you also need to provide [huggingface token](https://huggingface.co/docs/hub/security-tokens) to "HUGGINGFACEHUB_API_TOKEN" environment variable.

### 2.1 Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export host_ip="host_ip_address_or_dns_name"
export DBQNA_HUGGINGFACEHUB_API_TOKEN=""
export DBQNA_TGI_SERVICE_PORT=8008
export DBQNA_TGI_LLM_ENDPOINT="http://${host_ip}:${DBQNA_TGI_SERVICE_PORT}"
export DBQNA_LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="testpwd"
export POSTGRES_DB="chinook"
export DBQNA_TEXT_TO_SQL_PORT=18142
export DBQNA_UI_PORT=18143
```

Note: Please replace with `host_ip_address_or_dns_name` with your external IP address or DNS name, do not use localhost.

### 2.2 Start Microservice Docker Containers

There are 2 options to start the microservice

#### 2.2.1 Start the microservice using docker compose

```bash
cd GenAIExamples/DBQnA/docker_compose/amd/gpu/rocm
docker compose up -d
```

## 🚀 Validate Microservices

### 3.1 TGI Service

```bash
curl http://${host_ip}:$DBQNA_TGI_SERVICE_PORT/generate \
    -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
    -H 'Content-Type: application/json'
```

### 3.2 Postgres Microservice

Once Text-to-SQL microservice is started, user can use below command

#### 3.2.1 Test the Database connection

```bash
curl --location http://${host_ip}:${DBQNA_TEXT_TO_SQL_PORT}/v1/postgres/health \
    --header 'Content-Type: application/json' \
    --data '{"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${host_ip}'", "port": "5442", "database": "'${POSTGRES_DB}'"}'
```

#### 3.2.2 Invoke the microservice.

```bash
curl http://${host_ip}:${DBQNA_TEXT_TO_SQL_PORT}/v1/texttosql \
    -X POST \
    -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${host_ip}'", "port": "5442", "database": "'${POSTGRES_DB}'"}}' \
    -H 'Content-Type: application/json'
```

### 3.3 Frontend validation

We test the API in frontend validation to check if API returns HTTP_STATUS: 200 and validates if API response returns SQL query and output

The test is present in App.test.tsx under react root folder ui/react/

Command to run the test

```bash
npm run test
```

## 🚀 Launch the React UI

Open this URL `http://${host_ip}:${DBQNA_UI_PORT}` in your browser to access the frontend.

![project-screenshot](../../../../assets/img/dbQnA_ui_init.png)

Test DB Connection
![project-screenshot](../../../../assets/img/dbQnA_ui_successful_db_connection.png)

Create SQL query and output for given NLP question
![project-screenshot](../../../../assets/img/dbQnA_ui_succesful_sql_output_generation.png)
