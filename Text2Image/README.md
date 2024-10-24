# Text-to-Image Microservice

Text-to-Image is a task that generate image conditioning on the provided text. This microservice supports text-to-image task by using Stable Diffusion (SD) model.

## Deploy Text-to-Image Service

### Deploy Text-to-Image Service on Xeon

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for detail.

### Deploy Text-to-Image Service on Gaudi

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) for detail.

## Consume Text-to-Image Service

Use below command to generate image.

```bash
http_proxy="" curl http://localhost:9379/v1/text2image -XPOST -d '{"prompt":"An astronaut riding a green horse", "num_images_per_prompt":1}' -H 'Content-Type: application/json'
```
