<h1 align="center" id="title">Deploy ChatQnA in Kubernetes Cluster on Xeon</h1>

## Prebuilt images

You should have all the images

- redis-vector-db: redis/redis-stack:7.2.0-v9
- tei_embedding_service: ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
- embedding: opea/embedding-tei:latest
- retriever: opea/retriever-redis:latest
- tei_xeon_service: ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
- reranking: opea/reranking-tei:latest
- tgi_service: ghcr.io/huggingface/text-generation-inference:1.4
- llm: opea/llm-tgi:latest
- chaqna-xeon-backend-server: opea/chatqna:latest

For Gaudi:

- tei-embedding-service: opea/tei-gaudi:latest
- tgi-service: ghcr.io/huggingface/tgi-gaudi:1.2.1

> [NOTE]  
> Please refer README [for Xeon](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker-composer/xeon/README.md) and [for Gaudi](https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker-composer/gaudi/README.md) to build the opea images

## Deploy Services with Xeon

> [NOTE]

- Be sure to modify HF_TOKEN and other important values in qna_configmap_guadi.yaml and qna_configmap_xeon.yaml
- Be sure the node has path /mnt/models to store all the models

### Deploy

```
# Deploy Services with Xeon

$ cd ${RepoPath}/ChatQnA/kubernetes/manifests/
$ ./install_all_xeon.sh
```

### Undeploy

```
# Remove Services with Xeon

$ ./remove_all_xeon.sh
```

## Deploy Services with Gaudi

> [NOTE]
> Be sure to modify the all the important value in qna_configmap.yaml
> Be sure the node has path /mnt/models to store all the models

### Deploy

```
$ cd ${RepoPath}/ChatQnA/kubernetes/manifests/
$ ./install_all_gaudi.sh
```

### Undeploy

```
# Remove Services with Xeon
$ ./remove_all_gaudi.sh
```

## Verify Services

```
$ chaqna_backend_svc_ip=`kubectl get svc|grep '^chaqna-xeon-backend-server-svc'|awk '{print $3}'` && echo ${chaqna_backend_svc_ip}
$ curl http://${chaqna_backend_svc_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
     "messages": "What is the revenue of Nike in 2023?"
     }'
```
