# Generative AI Examples

## Introduction

GenAIExamples are designed to give developers an easy entry into generative AI, featuring microservice-based samples that simplify the processes of deploying, testing, and scaling GenAI applications. All examples are fully compatible with Docker and Kubernetes, supporting a wide range of hardware platforms such as Gaudi, Xeon, and NVIDIA GPU, and other hardwares, ensuring flexibility and efficiency for your GenAI adoption.

## Architecture

[GenAIComps](https://github.com/opea-project/GenAIComps) is a service-based tool that includes microservice components such as llm, embedding, reranking, and so on. Using these components, various examples in GenAIExample can be constructed, including ChatQnA, DocSum, etc.

[GenAIInfra](https://github.com/opea-project/GenAIInfra), part of the OPEA containerization and cloud-native suite, enables quick and efficient deployment of GenAIExamples in the cloud.

[GenAIEval](https://github.com/opea-project/GenAIEval) measures service performance metrics such as throughput, latency, and accuracy for GenAIExamples. This feature helps users compare performance across various hardware configurations easily.

## Documentation

The GenAIExamples [documentation](https://opea-project.github.io/latest/examples/index.html) contains a comprehensive guide on all available examples including architecture, deployment guides, and more. Information on GenAIComps, GenAIInfra, and GenAIEval can also be found there.

## Getting Started

GenAIExamples offers flexible deployment options that cater to different user needs, enabling efficient use and deployment in various environments. Here’s a brief overview of the three primary methods: Python startup, Docker Compose, and Kubernetes.

Users can choose the most suitable approach based on ease of setup, scalability needs, and the environment in which they are operating.

### Deployment Guide

Deployment is based on released docker images by default, check [docker image list](./docker_images_list.md) for detailed information. You can also build your own images following instructions.

#### Prerequisite

- For Docker Compose based deployment, you should have docker compose installed. Refer to [docker compose install](https://docs.docker.com/compose/install/).
- For Kubernetes based deployment, you can use [Helm](https://helm.sh) or [GMC](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector/README.md) based deployment.

  - You should have a kubernetes cluster ready for use. If not, you can refer to [k8s install](https://github.com/opea-project/docs/tree/main/guide/installation/k8s_install/README.md) to deploy one.
  - (Optional) You should have Helm (version >= 3.15) installed if you want to deploy with Helm Charts. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.
  - (Optional) You should have GMC installed to your kubernetes cluster if you want to try with GMC. Refer to [GMC install](https://github.com/opea-project/docs/blob/main/guide/installation/gmc_install/gmc_install.md) for more information.

- Recommended Hardware Reference

  Based on different deployment model size and performance requirement, you may choose different hardware platforms or cloud instances. Here are some reference platforms

  | Use Case | Deployment model          | Reference Configuration                                              | Hardware access/instances                                                    |
  | -------- | ------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
  | Xeon     | Intel/neural-chat-7b-v3-3 | 64 vCPUs, 365 GB disk 100 GB RAM, and Ubuntu 24.04                   | visit the [[Intel Tiber Developer Cloud]](https://console.cloud.intel.com/). |
  | Gaudi    | Intel/neural-chat-7b-v3-3 | 1 or 2 Gaudi Card, 16vCPUs, 365 GB disk 100 GB RAM, and Ubuntu 24.04 | visit the [[Intel Tiber Developer Cloud]](https://console.cloud.intel.com/). |
  | Xeon     | Intel/neural-chat-7b-v3-3 | 64 vCPUs, 100 GB disk 64 GB RAM, and Ubuntu 24.04                    | AWS Cloud/c7i.16xlarge                                                       |

#### Deploy Examples

> **Note**: Check for [sample guides](https://opea-project.github.io/latest/examples/index.html) first for your use case. If it is not available, then refer to the table below.

| Use Case          | Docker Compose<br/>Deployment on Xeon                                          | Docker Compose<br/>Deployment on Gaudi                                       | Docker Compose<br/>Deployment on ROCm                                    | Kubernetes with Helm Charts                                         | Kubernetes with GMC                                          |
| ----------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- | ------------------------------------------------------------ |
| ChatQnA           | [Xeon Instructions](ChatQnA/docker_compose/intel/cpu/xeon/README.md)           | [Gaudi Instructions](ChatQnA/docker_compose/intel/hpu/gaudi/README.md)       | [ROCm Instructions](ChatQnA/docker_compose/amd/gpu/rocm/README.md)       | [ChatQnA with Helm Charts](ChatQnA/kubernetes/helm/README.md)       | [ChatQnA with GMC](ChatQnA/kubernetes/gmc/README.md)         |
| CodeGen           | [Xeon Instructions](CodeGen/docker_compose/intel/cpu/xeon/README.md)           | [Gaudi Instructions](CodeGen/docker_compose/intel/hpu/gaudi/README.md)       | [ROCm Instructions](CodeGen/docker_compose/amd/gpu/rocm/README.md)       | [CodeGen with Helm Charts](CodeGen/kubernetes/helm/README.md)       | [CodeGen with GMC](CodeGen/kubernetes/gmc/README.md)         |
| CodeTrans         | [Xeon Instructions](CodeTrans/docker_compose/intel/cpu/xeon/README.md)         | [Gaudi Instructions](CodeTrans/docker_compose/intel/hpu/gaudi/README.md)     | [ROCm Instructions](CodeTrans/docker_compose/amd/gpu/rocm/README.md)     | [CodeTrans with Helm Charts](CodeTrans/kubernetes/helm/README.md)   | [CodeTrans with GMC](CodeTrans/kubernetes/gmc/README.md)     |
| DocSum            | [Xeon Instructions](DocSum/docker_compose/intel/cpu/xeon/README.md)            | [Gaudi Instructions](DocSum/docker_compose/intel/hpu/gaudi/README.md)        | [ROCm Instructions](DocSum/docker_compose/amd/gpu/rocm/README.md)        | [DocSum with Helm Charts](DocSum/kubernetes/helm/README.md)         | [DocSum with GMC](DocSum/kubernetes/gmc/README.md)           |
| SearchQnA         | [Xeon Instructions](SearchQnA/docker_compose/intel/cpu/xeon/README.md)         | [Gaudi Instructions](SearchQnA/docker_compose/intel/hpu/gaudi/README.md)     | Not Supported                                                            | [SearchQnA with Helm Charts](SearchQnA/kubernetes/helm/README.md)   | [SearchQnA with GMC](SearchQnA/kubernetes/gmc/README.md)     |
| FaqGen            | [Xeon Instructions](FaqGen/docker_compose/intel/cpu/xeon/README.md)            | [Gaudi Instructions](FaqGen/docker_compose/intel/hpu/gaudi/README.md)        | [ROCm Instructions](FaqGen/docker_compose/amd/gpu/rocm/README.md)        | [FaqGen with Helm Charts](FaqGen/kubernetes/helm/README.md)         | Not supported                                                |
| Translation       | [Xeon Instructions](Translation/docker_compose/intel/cpu/xeon/README.md)       | [Gaudi Instructions](Translation/docker_compose/intel/hpu/gaudi/README.md)   | [ROCm Instructions](Translation/docker_compose/amd/gpu/rocm/README.md)   | Not Supported                                                       | [Translation with GMC](Translation/kubernetes/gmc/README.md) |
| AudioQnA          | [Xeon Instructions](AudioQnA/docker_compose/intel/cpu/xeon/README.md)          | [Gaudi Instructions](AudioQnA/docker_compose/intel/hpu/gaudi/README.md)      | [ROCm Instructions](AudioQnA/docker_compose/amd/gpu/rocm/README.md)      | [AudioQnA with Helm Charts](AudioQnA/kubernetes/helm/README.md)     | [AudioQnA with GMC](AudioQnA/kubernetes/gmc/README.md)       |
| VisualQnA         | [Xeon Instructions](VisualQnA/docker_compose/intel/cpu/xeon/README.md)         | [Gaudi Instructions](VisualQnA/docker_compose/intel/hpu/gaudi/README.md)     | [ROCm Instructions](VisualQnA/docker_compose/amd/gpu/rocm/README.md)     | [VisualQnA with Helm Charts](VisualQnA/kubernetes/helm/README.md)   | [VisualQnA with GMC](VisualQnA/kubernetes/gmc/README.md)     |
| MultimodalQnA     | [Xeon Instructions](MultimodalQnA/docker_compose/intel/cpu/xeon/README.md)     | [Gaudi Instructions](MultimodalQnA/docker_compose/intel/hpu/gaudi/README.md) | [ROCm Instructions](MultimodalQnA/docker_compose/amd/gpu/rocm/README.md) | Not supported                                                       | Not supported                                                |
| ProductivitySuite | [Xeon Instructions](ProductivitySuite/docker_compose/intel/cpu/xeon/README.md) | Not Supported                                                                | Not Supported                                                            | Not Supported                                                       | Not Supported                                                |
| Text2Image        | [Xeon Instructions](Text2Image/docker_compose/intel/cpu/xeon/README.md)        | [Gaudi Instructions](Text2Image/docker_compose/intel/hpu/gaudi/README.md)    | Not Supported                                                            | [Text2Image with Helm Charts](Text2Image/kubernetes/helm/README.md) | Not Supported                                                |

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
- [Legal Information](LEGAL_INFORMATION.md)
