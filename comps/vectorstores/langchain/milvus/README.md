# Start Milvus server

## 1. Configuration

Configure your Milvus instance to suit your application scenarios by adjusting corresponding parameters in milvus.yaml. Please refer to this [link](https://milvus.io/docs/configure-docker.md#Modify-the-configuration-file).
Customized the path to store data, default is /volumes

```bash
export DOCKER_VOLUME_DIRECTORY=${your_path}
```

## 2. Run Milvus service

```bash
docker compose up -d
```
