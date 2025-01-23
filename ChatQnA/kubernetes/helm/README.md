# Deploy ChatQnA on Kubernetes cluster

- You should have Helm (version >= 3.15) installed. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.
- For more deploy options, refer to [helm charts README](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts#readme).

## Deploy on Xeon

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install chatqna oci://ghcr.io/opea-project/charts/chatqna  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f cpu-values.yaml
```

## Deploy on Gaudi

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install chatqna oci://ghcr.io/opea-project/charts/chatqna  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f gaudi-vllm-values.yaml
```

## Deploy variants of ChatQnA

ChatQnA is configurable and you can enable/disable features by providing values.yaml file.
For example, to run with tgi instead of vllm inference engine on Gaudi hardware, use gaudi-tgi-values.yaml file:

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install chatqna oci://ghcr.io/opea-project/charts/chatqna  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f gaudi-tgi-values.yaml
```

See other *-values.yaml files in this directory for more reference.
