# Benchmarking Deployment

This document guides you through deploying this example pipelines using Helm charts. Helm charts simplify managing Kubernetes applications by packaging configuration and resources.

## Getting Started

### Preparation

```bash
# on k8s-master node
cd GenAIExamples/{example_name}/benchmark/performance/helm_charts

# Replace the key of HUGGINGFACEHUB_API_TOKEN with your actual Hugging Face token:
# vim hpu_with_rerank.yaml or hpu_without_rerank.yaml
HUGGINGFACEHUB_API_TOKEN: hf_xxxxx
```

### Deployment

```bash
# Deploy a ChatQnA pipeline using the specified YAML configuration.
# To deploy with different configurations, simply provide a different YAML file.
python deployment.py --workflow=with_rerank --mode=tuned --num_nodes=1
```
