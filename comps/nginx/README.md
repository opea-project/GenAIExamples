# Nginx for Microservice Forwarding

[Nginx](https://nginx.org/en/) serves as a versatile tool in the realm of web services, functioning as an HTTP and reverse proxy server, and a generic TCP/UDP proxy server.

In GenAIComps, we utilize nginx to streamline our network services. We provide an nginx Docker container, which is essential for deploying [OPEA](https://github.com/opea-project) microservices, mega services, and managing endpoint and port forwarding for frontend services. Our use of Docker to launch nginx ensures a flexible and reliable service deployment, optimizing our infrastructure to meet diverse operational demands.

## 🚀1. Build Docker Image

```bash
cd docker
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./Dockerfile .
```

## 🚀2. Environment Settings

To use Nginx for service forwarding, users need to setup environment variables first. The variables set here will be substituted in `nginx.conf.template`.

For example, if you want to use Nginx to forward the frontend, backend services of a [ChatQnA](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA) example, setup environment variables as below.

```bash
export FRONTEND_SERVICE_IP=${your_frontend_service_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=chatqna
export BACKEND_SERVICE_IP=${your_backend_service_ip}
export BACKEND_SERVICE_PORT=8888
export NGINX_PORT=${your_nginx_port}
```

Nginx will expose `80` as the default port. You can choose other available ports as `${your_nginx_port}` for Nginx docker.

For other examples, change the variable above following the corresponding READMEs.

If you want to forward other services like `dataprep` using Nginx, add the code below in `nginx.conf.template` and setup the right parameters for it. Notice that the `${dataprep_service_endpoint}` need to be the form of `/v1/xxx/xxx`.

```bash
location ${dataprep_service_endpoint} {
    proxy_pass http://${dataprep_service_ip}:${dataprep_service_port};
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 🚀3. Start Nginx Service

### 3.1 Start with CLI (Option 1)

```bash
docker run -d --name opea-nginx -p ${NGINX_PORT}:80 \
	-e FRONTEND_SERVICE_IP=${FRONTEND_SERVICE_IP} \
	-e FRONTEND_SERVICE_PORT=${FRONTEND_SERVICE_PORT} \
	-e BACKEND_SERVICE_NAME=${BACKEND_SERVICE_NAME} \
    -e BACKEND_SERVICE_IP=${BACKEND_SERVICE_IP} \
    -e BACKEND_SERVICE_PORT=${BACKEND_SERVICE_PORT} \
    opea/nginx:latest
```

### 3.2 Start with Docker Compose (Option 2)

```bash
cd docker
docker compose -f docker_compose.yaml up -d
```

## 🚀4. Consume Forwarded Service

To consume the backend service, use the curl command as below (this is a ChatQnA service example):

```bash
curl http://${your_nginx_ip}:${your_nginx_port}/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{"messages": "What is Deep Learning?"}'
```

For the frontend service, open the following URL in your browser: `http://${your_nginx_ip}:${your_nginx_port}`.
