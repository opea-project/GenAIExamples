# 🛢🔗 Text-to-SQL Microservice with Langchain

This README provides set-up instructions and comprehensive details regarding the Text-to-SQL microservices via LangChain. In this configuration, we will employ PostgresDB as our example database to showcase this microservice.

---

## 🚀 Start Microservice with Python（Option 1）

### Install Requirements

```bash
pip install -r requirements.txt
```

### Start PostgresDB Service

We will use [Chinook](https://github.com/lerocha/chinook-database) sample database as a default to test the Text-to-SQL microservice. Chinook database is a sample database ideal for demos and testing ORM tools targeting single and multiple database servers.

```bash
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook

cd comps/texttosql/langchain

docker run --name postgres-db --ipc=host -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p 5442:5432 -d -v ./chinook.sql:/docker-entrypoint-initdb.d/chinook.sql postgres:latest
```

### Start TGI Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export TGI_PORT=8008

docker run -d --name="texttosql-tgi-endpoint" --ipc=host -p $TGI_PORT:80 -v ./data:/data --shm-size 1g -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${LLM_MODEL_ID} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id $LLM_MODEL_ID
```

### Verify the TGI Service

```bash
export your_ip=$(hostname -I | awk '{print $1}')
curl http://${your_ip}:${TGI_PORT}/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### Setup Environment Variables

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"
```

### Start Text-to-SQL Microservice with Python Script

Start Text-to-SQL microservice with below command.

```bash
python3 main.py
```

---

## 🚀 Start Microservice with Docker (Option 2)

### Start PostGreSQL Database Service

Please refer to section [Start PostgresDB Service](#start-postgresdb-service)

### Start TGI Service

Please refer to section [Start TGI Service](#start-tgi-service)

### Setup Environment Variables

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"
```

### Build Docker Image

```bash
cd GenAIComps/
docker build -t opea/texttosql:latest -f comps/texttosql/langchain/Dockerfile .
```

#### Run Docker with CLI (Option A)

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"

docker run  --runtime=runc --name="comps-langchain-texttosql"  -p 9090:8080 --ipc=host -e llm_endpoint_url=${TGI_LLM_ENDPOINT} opea/texttosql:latest
```

#### Run via docker compose (Option B)

- Setup Environment Variables.

  ```bash
  export TGI_LLM_ENDPOINT=http://${your_ip}:${TGI_PORT}
  export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
  export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
  export POSTGRES_USER=postgres
  export POSTGRES_PASSWORD=testpwd
  export POSTGRES_DB=chinook
  ```

- Start the services.

  ```bash
  docker compose -f docker_compose_texttosql.yaml up
  ```

---

## ✅ Invoke the microservice.

The Text-to-SQL microservice exposes the following API endpoints:

- Test Database Connection

  ```bash
  curl --location http://${your_ip}:9090/v1/postgres/health \
  --header 'Content-Type: application/json' \
  --data '{"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${your_ip}'", "port": "5442", "database": "'${POSTGRES_DB}'"}'
  ```

- Execute SQL Query from input text

  ```bash
  curl http://${your_ip}:9090/v1/texttosql\
          -X POST \
          -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${your_ip}'", "port": "5442", "database": "'${POSTGRES_DB}'"}}' \
          -H 'Content-Type: application/json'
  ```
