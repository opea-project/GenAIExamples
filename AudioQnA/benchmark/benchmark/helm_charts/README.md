# Benchmarking Deployment

This document guides you through deploying this example pipeline using Helm charts. Helm charts simplify managing Kubernetes applications by packaging configuration and resources.

## Getting Started

### Preparation

```bash
# on k8s-master node
cd GenAIExamples/{example_name}/benchmark/performance/helm_charts

# Replace the key of HUGGINGFACEHUB_API_TOKEN with your actual Hugging Face token:
# vim values.yaml
HUGGINGFACEHUB_API_TOKEN: hf_xxxxx
```

### Deployment

```bash
# Deploy the pipeline
helm install {example_name} .
```
