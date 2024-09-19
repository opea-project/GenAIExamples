# Generative AI Examples

[![version](https://img.shields.io/badge/release-0.9-green)](https://github.com/opea-project/GenAIExamples/releases)
[![license](https://img.shields.io/badge/license-Apache%202-blue)](https://github.com/intel/neural-compressor/blob/master/LICENSE)

---

## Introduction

GenAIExamples are designed to give developers an easy entry into generative AI, featuring microservice-based samples that simplify the processes of deploying, testing, and scaling GenAI applications. All examples are fully compatible with Docker and Kubernetes, supporting a wide range of hardware platforms such as Gaudi, Xeon, and NVIDIA GPU, and other hardwares, ensuring flexibility and efficiency for your GenAI adoption.

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

| Use Case          | Docker Compose<br/>Deployment on Xeon                                          | Docker Compose<br/>Deployment on Gaudi                                     | Kubernetes with Manifests                                                        | Kubernetes with Helm Charts                                                                                        | Kubernetes with GMC                                                |
| ----------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| ChatQnA           | [Xeon Instructions](ChatQnA/docker_compose/intel/cpu/xeon/README.md)           | [Gaudi Instructions](ChatQnA/docker_compose/intel/hpu/gaudi/README.md)     | [ChatQnA with Manifests](ChatQnA/kubernetes/intel/README.md)                     | [ChatQnA with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/chatqna/README.md)     | [ChatQnA with GMC](ChatQnA/kubernetes/intel/README_gmc.md)         |
| CodeGen           | [Xeon Instructions](CodeGen/docker_compose/intel/cpu/xeon/README.md)           | [Gaudi Instructions](CodeGen/docker_compose/intel/hpu/gaudi/README.md)     | [CodeGen with Manifests](CodeGen/kubernetes/intel/README.md)                     | [CodeGen with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/codegen/README.md)     | [CodeGen with GMC](CodeGen/kubernetes/intel/README_gmc.md)         |
| CodeTrans         | [Xeon Instructions](CodeTrans/docker_compose/intel/cpu/xeon/README.md)         | [Gaudi Instructions](CodeTrans/docker_compose/intel/hpu/gaudi/README.md)   | [CodeTrans with Manifests](CodeTrans/kubernetes/intel/README.md)                 | [CodeTrans with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/codetrans/README.md) | [CodeTrans with GMC](CodeTrans/kubernetes/intel/README_gmc.md)     |
| DocSum            | [Xeon Instructions](DocSum/docker_compose/intel/cpu/xeon/README.md)            | [Gaudi Instructions](DocSum/docker_compose/intel/hpu/gaudi/README.md)      | [DocSum with Manifests](DocSum/kubernetes/intel/README.md)                       | [DocSum with Helm Charts](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/docsum/README.md)       | [DocSum with GMC](DocSum/kubernetes/intel/README_gmc.md)           |
| SearchQnA         | [Xeon Instructions](SearchQnA/docker_compose/intel/cpu/xeon/README.md)         | [Gaudi Instructions](SearchQnA/docker_compose/intel/hpu/gaudi/README.md)   | Not Supported                                                                    | Not Supported                                                                                                      | [SearchQnA with GMC](SearchQnA/kubernetes/intel/README_gmc.md)     |
| FaqGen            | [Xeon Instructions](FaqGen/docker_compose/intel/cpu/xeon/README.md)            | [Gaudi Instructions](FaqGen/docker_compose/intel/hpu/gaudi/README.md)      | [FaqGen with Manifests](FaqGen/kubernetes/intel/README.md)                       | Not Supported                                                                                                      | [FaqGen with GMC](FaqGen/kubernetes/intel/README_gmc.md)           |
| Translation       | [Xeon Instructions](Translation/docker_compose/intel/cpu/xeon/README.md)       | [Gaudi Instructions](Translation/docker_compose/intel/hpu/gaudi/README.md) | [Translation with Manifests](Translation/kubernetes/intel/README.md)             | Not Supported                                                                                                      | [Translation with GMC](Translation/kubernetes/intel/README_gmc.md) |
| AudioQnA          | [Xeon Instructions](AudioQnA/docker_compose/intel/cpu/xeon/README.md)          | [Gaudi Instructions](AudioQnA/docker_compose/intel/hpu/gaudi/README.md)    | [AudioQnA with Manifests](AudioQnA/kubernetes/intel/README.md)                   | Not Supported                                                                                                      | [AudioQnA with GMC](AudioQnA/kubernetes/intel/README_gmc.md)       |
| VisualQnA         | [Xeon Instructions](VisualQnA/docker_compose/intel/cpu/xeon/README.md)         | [Gaudi Instructions](VisualQnA/docker_compose/intel/hpu/gaudi/README.md)   | [VisualQnA with Manifests](VisualQnA/kubernetes/intel/README.md)                 | Not Supported                                                                                                      | [VisualQnA with GMC](VisualQnA/kubernetes/intel/README_gmc.md)     |
| ProductivitySuite | [Xeon Instructions](ProductivitySuite/docker_compose/intel/cpu/xeon/README.md) | Not Supported                                                              | [ProductivitySuite with Manifests](ProductivitySuite/kubernetes/intel/README.md) | Not Supported                                                                                                      | Not Supported                                                      |

## Supported Examples

Check [here](./supported_examples.md) for detailed information of supported examples, models, hardwares, etc.

## Contributing to OPEA

Welcome to the OPEA open-source community! We are thrilled to have you here and excited about the potential contributions you can bring to the OPEA platform. Whether you are fixing bugs, adding new GenAI components, improving documentation, or sharing your unique use cases, your contributions are invaluable.

Together, we can make OPEA the go-to platform for enterprise AI solutions. Let's work together to push the boundaries of what's possible and create a future where AI is accessible, efficient, and impactful for everyone.

Please check the [Contributing guidelines](https://github.com/opea-project/docs/tree/main/community/CONTRIBUTING.md) for a detailed guide on how to contribute a GenAI component and all the ways you can contribute!

Thank you for being a part of this journey. We can't wait to see what we can achieve together!

## Additional Content

- [Code of Conduct](https://github.com/opea-project/docs/tree/main/community/CODE_OF_CONDUCT.md)
- [Security Policy](https://github.com/opea-project/docs/tree/main/community/SECURITY.md)
- [Legal Information](/LEGAL_INFORMATION.md)
