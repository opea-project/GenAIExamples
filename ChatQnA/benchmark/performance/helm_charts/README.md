# ChatQnA Deployment

This document guides you through deploying ChatQnA pipelines using Helm charts. Helm charts simplify managing Kubernetes applications by packaging configuration and resources.

## Getting Started

### Preparation

```bash
# on k8s-master node
cd GenAIExamples/ChatQnA/benchmark/performance/helm_charts

# Replace the key of HUGGINGFACEHUB_API_TOKEN with your actual Hugging Face token:
# vim customize.yaml
HUGGINGFACEHUB_API_TOKEN: hf_xxxxx
```

### Deploy your ChatQnA

```bash
# Deploy a ChatQnA pipeline using the specified YAML configuration.
# To deploy with different configurations, simply provide a different YAML file.
helm install chatqna helm_charts/ -f customize.yaml
```

Notes: The provided [BKC manifests](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/benchmark) for single, two, and four node Kubernetes clusters are generated using this tool.

## Customize your own ChatQnA pipelines. (Optional)

There are two yaml configs you can specify.

- customize.yaml
  This file can specify image names, the number of replicas and CPU cores to manage your pods.

- values.yaml
  This file contains the default microservice configurations for ChatQnA. Please review and understand each parameter before making any changes.
