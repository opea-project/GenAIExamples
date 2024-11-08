# DocSum

Helm chart for deploying DocSum service.

DocSum depends on LLM microservice, refer to llm-uservice for more config details.

## Installing the Chart

To install the chart, run the following:

```console
cd GenAIInfra/helm-charts/
./update_dependency.sh
helm dependency update docsum
export HFTOKEN="insert-your-huggingface-token-here"
export MODELDIR="/mnt/opea-models"
export MODELNAME="Intel/neural-chat-7b-v3-3"
helm install docsum docsum --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --set global.modelUseHostPath=${MODELDIR} --set tgi.LLM_MODEL_ID=${MODELNAME}
# To use Gaudi device
# helm install docsum docsum --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} --values docsum/gaudi-values.yaml
```

## Verify

To verify the installation, run the command `kubectl get pod` to make sure all pods are running.

Curl command and UI are the two options that can be leveraged to verify the result.

### Verify the workload through curl command

Then run the command `kubectl port-forward svc/docsum 8888:8888` to expose the DocSum service for access.

Open another terminal and run the following command to verify the service if working:

```console
curl http://localhost:8888/v1/docsum \
    -H 'Content-Type: application/json' \
    -d '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
```

### Verify the workload through UI

The UI has already been installed via the Helm chart. To access it, use the external IP of one your Kubernetes node along with the NGINX port. You can find the NGINX port using the following command:

```bash
export port=$(kubectl get service docsum-nginx --output='jsonpath={.spec.ports[0].nodePort}')
echo $port
```

Open a browser to access `http://<k8s-node-ip-address>:${port}` to play with the ChatQnA workload.

## Values

| Key               | Type   | Default                       | Description                                                                            |
| ----------------- | ------ | ----------------------------- | -------------------------------------------------------------------------------------- |
| image.repository  | string | `"opea/docsum"`               |                                                                                        |
| service.port      | string | `"8888"`                      |                                                                                        |
| tgi.LLM_MODEL_ID  | string | `"Intel/neural-chat-7b-v3-3"` | Models id from https://huggingface.co/, or predownloaded model directory               |
| global.monitoring | bool   | `false`                       | Enable usage metrics for the service components. See ../monitoring.md before enabling! |
