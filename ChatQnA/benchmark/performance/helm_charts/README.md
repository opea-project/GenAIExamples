# ChatQnA Deployment

This document guides you through deploying ChatQnA pipelines using Helm charts. Helm charts simplify managing Kubernetes applications by packaging configuration and resources.

## Getting Started

### Preparation

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/helm_charts

# Replace <your token> with your actual Hugging Face token and run the following command:
HUGGINGFACE_TOKEN=<your token>
find . -name '*.yaml' -type f -exec sed -i "s#\${HF_TOKEN}#${HUGGINGFACE_TOKEN}#g" {} \;

# Replace the following placeholders with the desired model IDs:
LLM_MODEL_ID=Intel/neural-chat-7b-v3-3
EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
RERANK_MODEL_ID=BAAI/bge-reranker-base
find . -name '*.yaml' -type f -exec sed -i "s#\$(LLM_MODEL_ID)#${LLM_MODEL_ID}#g" {} \;
find . -name '*.yaml' -type f -exec sed -i "s#\$(EMBEDDING_MODEL_ID)#${EMBEDDING_MODEL_ID}#g" {} \;
find . -name '*.yaml' -type f -exec sed -i "s#\$(RERANK_MODEL_ID)#${RERANK_MODEL_ID}#g" {} \;

```

### ChatQnA Installation

```bash
# Deploy a ChatQnA pipeline using the specified YAML configuration.
# To deploy with different configurations, simply provide a different YAML file.
helm install chatqna helm_charts/ -f helm_charts/oob_single_node.yaml

# Tips: To display rendered manifests according to the given yaml.
helm template chatqna helm_charts/ -f helm_charts/oob_single_node.yaml
```

Notes: The provided [BKC manifests](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark) for single, two, and four node Kubernetes clusters are generated using this tool.
