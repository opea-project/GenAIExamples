# Deploy AudioQnA in a Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN
> You can also customize the "MODEL_ID" and "model-volume"

## Deploy On Xeon
```
cd GenAIExamples/AudioQnA/kubernetes/manifests/xeon
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" audioqna.yaml
kubectl apply -f audioqna.yaml
```
## Deploy On Gaudi
```
cd GenAIExamples/AudioQnA/kubernetes/manifests/gaudi
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" audioqna.yaml
kubectl apply -f audioqna.yaml
```


## Verify Services

Make sure all the pods are running, and restart the audioqna-xxxx pod if necessary.

```bash
kubectl get pods

curl http://${host_ip}:3008/v1/audioqna   -X POST   -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}'   -H 'Content-Type: application/json'
```
