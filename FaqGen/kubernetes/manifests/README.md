# Deploy FaqGen in Kubernetes Cluster

> [NOTE]
> The following values must be set before you can deploy:
> HUGGINGFACEHUB_API_TOKEN
> You can also customize the "MODEL_ID" and "model-volume"

## Deploy On Xeon

```
cd GenAIExamples/FaqGen/kubernetes/manifests/xeon
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" faqgen.yaml
kubectl apply -f faqgen.yaml
```

## Deploy On Gaudi

```
cd GenAIExamples/FaqGen/kubernetes/manifests/gaudi
export HUGGINGFACEHUB_API_TOKEN="YourOwnToken"
sed -i "s/insert-your-huggingface-token-here/${HUGGINGFACEHUB_API_TOKEN}/g" faqgen.yaml
kubectl apply -f faqgen.yaml
```

## Deploy UI

```
cd GenAIExamples/FaqGen/kubernetes/manifests/
kubectl get svc # get ip address
ip_address="" # according to your svc address
sed -i "s/insert_your_ip_here/${ip_address}/g" ui.yaml
kubectl apply -f ui.yaml
```

## Verify Services

Make sure all the pods are running, and restart the faqgen-xxxx pod if necessary.

```
kubectl get pods
port=7779 # 7779 for gaudi, 7778 for xeon
curl http://${host_ip}:7779/v1/faqgen -H "Content-Type: application/json" -d '{
     "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
     }'
```
