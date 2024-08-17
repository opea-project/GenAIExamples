<div align="center">

# Generative AI Examples

[![version](https://img.shields.io/badge/release-0.8-green)](https://github.com/opea-project/GenAIExamples/releases)
[![license](https://img.shields.io/badge/license-Apache%202-blue)](https://github.com/intel/neural-compressor/blob/master/LICENSE)

---

<div align="left">

## Introduction

GenAIComps-based Generative AI examples offer streamlined deployment, testing, and scalability. All examples are fully compatible with Docker and Kubernetes, supporting a wide range of hardware platforms such as Gaudi, Xeon, and other hardwares.

## Architecture

[GenAIComps](https://github.com/opea-project/GenAIComps) is a service-based tool that includes microservice components such as llm, embedding, reranking, and so on. Using these components, various examples in GenAIExample can be constructed, including ChatQnA, DocSum, etc.

[GenAIInfra](https://github.com/opea-project/GenAIInfra), part of the OPEA containerization and cloud-native suite, enables quick and efficient deployment of GenAIExamples in the cloud.

[GenAIEval](https://github.com/opea-project/GenAIEval) measures service performance metrics such as throughput, latency, and accuracy for GenAIExamples. This feature helps users compare performance across various hardware configurations easily.

## Getting Started

GenAIExamples offers flexible deployment options that cater to different user needs, enabling efficient use and deployment in various environments. Here’s a brief overview of the three primary methods: Python startup, Docker Compose, and Kubernetes.

1. <b>Docker Compose</b>: Check the released docker images in [docker image list](./docker_images_list.md) for detailed information.
2. <b>Kubernetes</b>: Follow the steps at [K8s Install](https://github.com/opea-project/docs/tree/main/guide/installation/k8s_install) and [GMC Install](https://github.com/opea-project/docs/blob/main/guide/installation/gmc_install/gmc_install.md) to setup k8s and GenAI environment .

Users can choose the most suitable approach based on ease of setup, scalability needs, and the environment in which they are operating.

### Deployment

| Use Case    | Docker Compose<br/>Deployment on Xeon                  | Docker Compose<br/>Deployment on Gaudi                   | Kubernetes Deployment                                     |
| ----------- | ------------------------------------------------------ | -------------------------------------------------------- | --------------------------------------------------------- |
| ChatQnA     | [Xeon Instructions](ChatQnA/docker/xeon/README.md)     | [Gaudi Instructions](ChatQnA/docker/gaudi/README.md)     | [K8s Instructions](ChatQnA/kubernetes/README.md)          |
| CodeGen     | [Xeon Instructions](CodeGen/docker/xeon/README.md)     | [Gaudi Instructions](CodeGen/docker/gaudi/README.md)     | [K8s Instructions](Codegen/kubernetes/README.md)          |
| CodeTrans   | [Xeon Instructions](CodeTrans/docker/xeon/README.md)   | [Gaudi Instructions](CodeTrans/docker/gaudi/README.md)   | [K8s Instructions](CodeTrans/kubernetes/README.md)        |
| DocSum      | [Xeon Instructions](CodeTrans/docker/xeon/README.md)   | [Gaudi Instructions](CodeTrans/docker/gaudi/README.md)   | [K8s Instructions](CodeTrans/kubernetes/README.md)        |
| SearchQnA   | [Xeon Instructions](SearchQnA/docker/xeon/README.md)   | [Gaudi Instructions](SearchQnA/docker/gaudi/README.md)   | [K8s Instructions](SearchQnA/kubernetes/README.md)        |
| FaqGen      | [Xeon Instructions](FaqGen/docker/xeon/README.md)      | [Gaudi Instructions](FaqGen/docker/gaudi/README.md)      | [K8s Instructions](FaqGen/kubernetes/manifests/README.md) |
| Translation | [Xeon Instructions](Translation/docker/xeon/README.md) | [Gaudi Instructions](Translation/docker/gaudi/README.md) | [K8s Instructions](Translation/kubernetes/README.md)      |
| AudioQnA    | [Xeon Instructions](AudioQnA/docker/xeon/README.md)    | [Gaudi Instructions](AudioQnA/docker/gaudi/README.md)    | K8s Not Supported                                         |
| VisualQnA   | [Xeon Instructions](VisualQnA/docker/xeon/README.md)   | [Gaudi Instructions](VisualQnA/docker/gaudi/README.md)   | K8s Not Supported                                         |

## Support Examples

Check [here](./supported_examples.md) for detailed information of supported examples, models, hardwares, etc.

## Additional Content

- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Contribution](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
