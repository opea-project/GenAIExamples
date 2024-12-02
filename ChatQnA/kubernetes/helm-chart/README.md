# ChatQnA

Helm chart for deploying ChatQnA service. ChatQnA depends on the following services:

- [data-prep](../common/data-prep/README.md)
- [embedding-usvc](../common/embedding-usvc/README.md)
- [tei](../common/tei/README.md)
- [retriever-usvc](../common/retriever-usvc/README.md)
- [redis-vector-db](../common/redis-vector-db/README.md)
- [reranking-usvc](../common/reranking-usvc/README.md)
- [teirerank](../common/teirerank/README.md)
- [llm-uservice](../common/llm-uservice/README.md)
- [tgi](../common/tgi/README.md)

## Installing the Chart

To install the chart, run the following:

```console
cd GenAIInfra/helm-charts/
./update_dependency.sh
helm dependency update chatqna
export HFTOKEN="insert-your-huggingface-token-here"
export MODELDIR="/mnt/opea-models"
export MODELNAME="Intel/neural-chat-7b-v3-3"
# If you would like to use the traditional UI, please change the image as well as the containerport within the values
# append these at the end of the command "--set chatqna-ui.image.repository=opea/chatqna-ui,chatqna-ui.image.tag=latest,chatqna-ui.containerPort=5173"
helm install chatqna chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --set global.modelUseHostPath=${MODELDIR} --set tgi.LLM_MODEL_ID=${MODELNAME}
# To use Gaudi device
#helm install chatqna chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --set global.modelUseHostPath=${MODELDIR} --set tgi.LLM_MODEL_ID=${MODELNAME} -f chatqna/gaudi-values.yaml
# To use Nvidia GPU
#helm install chatqna chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --set global.modelUseHostPath=${MODELDIR} --set tgi.LLM_MODEL_ID=${MODELNAME} -f chatqna/nv-values.yaml
# To include guardrail component in chatqna on Xeon
#helm install chatqna chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --set global.modelUseHostPath=${MODELDIR} -f chatqna/guardrails-values.yaml
# To include guardrail component in chatqna on Gaudi
#helm install chatqna chatqna --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --set global.modelUseHostPath=${MODELDIR} -f chatqna/guardrails-gaudi-values.yaml
```

### IMPORTANT NOTE

1. Make sure your `MODELDIR` exists on the node where your workload is scheduled so you can cache the downloaded model for next time use. Otherwise, set `global.modelUseHostPath` to 'null' if you don't want to cache the model.

## Verify

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Curl command and UI are the two options that can be leveraged to verify the result.

### Verify the workload through curl command

Run the command `kubectl port-forward svc/chatqna 8888:8888` to expose the service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{"messages": "What is the revenue of Nike in 2023?"}'
```

### Verify the workload through UI

The UI has already been installed via the Helm chart. To access it, use the external IP of one your Kubernetes node along with the NGINX port. You can find the NGINX port using the following command:

```bash
export port=$(kubectl get service chatqna-nginx --output='jsonpath={.spec.ports[0].nodePort}')
echo $port
```

Open a browser to access `http://<k8s-node-ip-address>:${port}` to play with the ChatQnA workload.

## Values

| Key               | Type   | Default                       | Description                                                                            |
| ----------------- | ------ | ----------------------------- | -------------------------------------------------------------------------------------- |
| image.repository  | string | `"opea/chatqna"`              |                                                                                        |
| service.port      | string | `"8888"`                      |                                                                                        |
| tgi.LLM_MODEL_ID  | string | `"Intel/neural-chat-7b-v3-3"` | Models id from https://huggingface.co/, or predownloaded model directory               |
| global.monitoring | bool   | `false`                       | Enable usage metrics for the service components. See ../monitoring.md before enabling! |

## Troubleshooting

If you encounter any issues, please refer to [ChatQnA Troubleshooting](troubleshooting.md)
