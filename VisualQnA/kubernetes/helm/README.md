# Deploy VisualQnA on Kubernetes cluster

- You should have Helm (version >= 3.15) installed. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.
- For more deploy options, refer to [helm charts README](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts#readme).

## Deploy on Xeon

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install visualqna oci://ghcr.io/opea-project/charts/visualqna  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f cpu-values.yaml
```

## Deploy on Gaudi

```
export HFTOKEN="insert-your-huggingface-token-here"
helm install visualqna oci://ghcr.io/opea-project/charts/visualqna  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} -f gaudi-values.yaml
```
