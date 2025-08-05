# Text-to-Image Microservice

Text-to-Image is a task that generates image conditioning on the provided text. This microservice supports text-to-image task by using Stable Diffusion (SD) model.

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

| Hardware                       | Deployment Approach | Deployment Guide                                         |
| ------------------------------ | ------------------- | -------------------------------------------------------- |
| Single-Node Intel Xeon System  | Docker Compose      | [View Guide](./docker_compose/intel/cpu/xeon/README.md)  |
| Single-Node Intel Gaudi System | Docker Compose      | [View Guide](./docker_compose/intel/hpu/gaudi/README.md) |
| Intel Xeon Cluster             | Helm                | [View Guide](./kubernetes/helm/README.md)                |
| Intel Gaudi Cluster            | Helm                | [View Guide](./kubernetes/helm/README.md)                |

### Deploy Text-to-Image Service on AMD EPYC

Refer to the [AMD EPYC Guide](./docker_compose/amd/cpu/epyc/README.md) for detail.

## Consume Text-to-Image Service

Use below command to generate image.

```bash
http_proxy="" curl http://localhost:9379/v1/text2image -XPOST -d '{"prompt":"An astronaut riding a green horse", "num_images_per_prompt":1}' -H 'Content-Type: application/json'
```

## Validated Configurations

| **Deploy Method** | **Hardware** |
| ----------------- | ------------ |
| Docker Compose    | Intel Xeon   |
| Docker Compose    | Intel Gaudi  |
| Docker Compose    | AMD EPYC     |
| Helm Charts       | Intel Gaudi  |
| Helm Charts       | Intel Xeon   |
