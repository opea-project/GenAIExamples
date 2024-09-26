# Text-to-SQL Microservice

In today's data-driven world, the ability to efficiently extract insights from databases is crucial. However, querying databases often requires specialized knowledge of SQL and database schemas, which can be a barrier for non-technical users. This is where the Text-to-SQL microservice comes into play, leveraging the power of LLMs and agentic frameworks to bridge the gap between human language and database queries. This microservice is built on Langchain/Langgraph frameworks.

The microservice enables a wide range of use cases, making it a versatile tool for businesses, researchers, and individuals alike. Users can generate queries based on natural language questions, enabling them to quickly retrieve relevant data from their databases. Additionally, the service can be integrated into chatbots, allowing for natural language interactions and providing accurate responses based on the underlying data. Furthermore, it can be utilized to build custom dashboards, enabling users to visualize and analyze insights based on their specific requirements, all through the power of natural language.

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start PostgresDB Service

We will use [Chinook](https://github.com/lerocha/chinook-database) sample database as a default to test the Text-to-SQL microservice. Chinook database is a sample database ideal for demos and testing ORM tools targeting single and multiple database servers.

```bash
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook

cd comps/texttosql/langchain

docker run --name postgres-db --ipc=host -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p 5442:5432 -d -v ./chinook.sql:/docker-entrypoint-initdb.d/chinook.sql postgres:latest
```

### 1.3 Start TGI Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export TGI_PORT=8008

docker run -d --name="texttosql-tgi-endpoint" --ipc=host -p $TGI_PORT:80 -v ./data:/data --shm-size 1g -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${LLM_MODEL_ID} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id $LLM_MODEL_ID
```

### 1.4 Verify the TGI Service

```bash

export your_ip=$(hostname -I | awk '{print $1}')
curl http://${your_ip}:${TGI_PORT}/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### 1.5 Setup Environment Variables

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"
```

### 1.6 Start Text-to-SQL Microservice with Python Script

Start Text-to-SQL microservice with below command.

```bash
python3 main.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start PostGreSQL Database Service

Please refer to 1.2.

### 2.2 Start TGI Service

Please refer to 1.3.

### 2.3 Setup Environment Variables

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"
```

### 2.4 Build Docker Image

```bash
cd GenAIComps/ # back to GenAIComps/ folder
docker build -t opea/texttosql:latest -f comps/texttosql/langchain/Dockerfile .
```

#### 2.5 Run Docker with CLI (Option A)

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"

docker run  --runtime=runc --name="comps-langchain-texttosql"  -p 9090:8080 --ipc=host -e llm_endpoint_url=${TGI_LLM_ENDPOINT} opea/texttosql:latest

```

#### 2.6 Run via docker compose. (Option B)

Set Environment Variables.

```bash
export TGI_LLM_ENDPOINT=http://${your_ip}:${TGI_PORT}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook
```

Start the services.

```bash
docker compose -f docker_compose_texttosql.yaml up
```

## 🚀3. Consume Microservice

Once Text-to-SQL microservice is started, user can use below command

- Test the Database connection

```bash
curl --location http://${your_ip}:9090/v1/postgres/health \
--header 'Content-Type: application/json' \
--data '{"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${your_ip}'", "port": "5442", "database": "'${POSTGRES_DB}'"}'
```

- Invoke the microservice.

```bash
curl http://${your_ip}:9090/v1/texttosql\
        -X POST \
        -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${your_ip}'", "port": "5442", "database": "'${POSTGRES_DB}'"}}' \
        -H 'Content-Type: application/json'
```
