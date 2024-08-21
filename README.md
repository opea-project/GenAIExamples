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

Users can choose the most suitable approach based on ease of setup, scalability needs, and the environment in which they are operating.

### Deployment Guide

Deployment are based on released docker images by default, check [docker image list](./docker_images_list.md) for detailed information. You can also build your own images following instructions.

#### Prerequisite

- For Docker Compose based deployment, you should have docker compose installed. Refer to [docker compose install](https://docs.docker.com/compose/install/).
- For Kubernetes based deployment, we provide 3 ways from the easiest manifests to powerful [GMC](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector) based deployment.
  - You should have a kubernetes cluster ready for use. If not, you can refer to [k8s install](https://github.com/opea-project/docs/tree/main/guide/installation/k8s_install) to deploy one.
  - (Optional) You should have GMC installed to your kubernetes cluster if you want to try with GMC. Refer to [GMC install](https://github.com/opea-project/docs/blob/main/guide/installation/gmc_install/gmc_install.md) for more information.
  - (Optional) You should have Helm (version >= 3.15) installed if you want to deploy with Helm Charts. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.

#### Deploy Examples

| Use Case    | Docker Compose<br/>Deployment on Xeon                  | Docker Compose<br/>Deployment on Gaudi                   | Kubernetes with GMC                                      | Kubernetes with Manifests                                            | Kubernetes with Helm Charts                                                                                        |
| ----------- | ------------------------------------------------------ | -------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| ChatQnA     | [Xeon Instructions](ChatQnA/docker/xeon/README.md)     | [Gaudi Instructions](ChatQnA/docker/gaudi/README.md)     | [ChatQnA with GMC](ChatQnA/kubernetes/README.md)         | [ChatQnA with Manifests](ChatQnA/kubernetes/manifests/README.md)     | [ChatQnA with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/chatqna/README.md)     |
| CodeGen     | [Xeon Instructions](CodeGen/docker/xeon/README.md)     | [Gaudi Instructions](CodeGen/docker/gaudi/README.md)     | [CodeGen with GMC](CodeGen/kubernetes/README.md)         | [CodeGen with Manifests](CodeGen/kubernetes/manifests/README.md)     | [CodeGen with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/codegen/README.md)     |
| CodeTrans   | [Xeon Instructions](CodeTrans/docker/xeon/README.md)   | [Gaudi Instructions](CodeTrans/docker/gaudi/README.md)   | [CodeTrans with GMC](CodeTrans/kubernetes/README.md)     | [CodeTrans with Manifests](CodeTrans/kubernetes/manifests/README.md) | [CodeTrans with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/codetrans/README.md) |
| DocSum      | [Xeon Instructions](DocSum/docker/xeon/README.md)      | [Gaudi Instructions](DocSum/docker/gaudi/README.md)      | [DocSum with GMC](DocSum/kubernetes/README.md)           | [DocSum with Manifests](DocSum/kubernetes/manifests/README.md)       | [DocSum with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/docsum/README.md)       |
| SearchQnA   | [Xeon Instructions](SearchQnA/docker/xeon/README.md)   | [Gaudi Instructions](SearchQnA/docker/gaudi/README.md)   | [SearchQnA with GMC](SearchQnA/kubernetes/README.md)     | Not Supported                                                        | Not Supported                                                                                                      |
| FaqGen      | [Xeon Instructions](FaqGen/docker/xeon/README.md)      | [Gaudi Instructions](FaqGen/docker/gaudi/README.md)      | [FaqGen with GMC](FaqGen/kubernetes/README.md)           | Not Supported                                                        | Not Supported                                                                                                      |
| Translation | [Xeon Instructions](Translation/docker/xeon/README.md) | [Gaudi Instructions](Translation/docker/gaudi/README.md) | [Translation with GMC](Translation/kubernetes/README.md) | Not Supported                                                        | Not Supported                                                                                                      |
| AudioQnA    | [Xeon Instructions](AudioQnA/docker/xeon/README.md)    | [Gaudi Instructions](AudioQnA/docker/gaudi/README.md)    | [AudioQnA with GMC](AudioQnA/kubernetes/README.md)       | Not Supported                                                        | Not Supported                                                                                                      |
| VisualQnA   | [Xeon Instructions](VisualQnA/docker/xeon/README.md)   | [Gaudi Instructions](VisualQnA/docker/gaudi/README.md)   | [VisualQnA with GMC](VisualQnA/kubernetes/README.md)     | Not Supported                                                        | Not Supported                                                                                                      |

## Supported Examples

Check [here](./supported_examples.md) for detailed information of supported examples, models, hardwares, etc.

## Additional Content

- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Contribution](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
