# Validated Configurations

This document provides an overview of the validated configurations for the GenAIExamples release test, including hardware and software versions that have been tested and confirmed to work together.
Example specific test matrix can be found in examples' README.md files, for example [ChatQnA Config](./ChatQnA/README.md#validated-configurations).

## v1.3 Release Test Config Overview

| **HW/SW Stake**        | **Description**                                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Validated Hardware** | Intel Gaudi AI Accelerators (2nd, 3rd)                                                                       |
|                        | Intel Xeon Scalable processor (4th, 6th)                                                                     |
|                        | Intel Arc Graphics GPU (A770)                                                                                |
|                        | AMD Instinct MI300X Accelerators (CDNA3)                                                                     |
| **Validated Software** | Ubuntu 22.04                                                                                                 |
|                        | Habana v1.20 ([link](https://docs.habana.ai/en/v1.20.1/Installation_Guide/index.html))                       |
|                        | ROCm v6.4.0 ([link](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/install/quick-start.html)) |
|                        | Docker version 28.0.4                                                                                        |
|                        | Docker Compose version v2.34.0                                                                               |
|                        | Kubernetes v1.29.15                                                                                          |
|                        | HabanaAI vLLM v0.6.6.post1+Gaudi-1.20.0                                                                      |
|                        | vLLM v0.8.3 (Xeon, ROCm)                                                                                     |
|                        | TGI v2.4.0 (Xeon), v2.3.1 (Gaudi), v2.4.1 (ROCm)                                                             |
|                        | TEI v1.6                                                                                                     |

## v1.4 Release Test Config Overview

| **HW/SW Stake**        | **Description**                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------- |
| **Validated Hardware** | Intel Gaudi AI Accelerators (2nd)                                                      |
|                        | Intel Xeon Scalable processor (3rd)                                                    |
|                        | Intel Arc Graphics GPU (A770)                                                          |
|                        | AMD EPYC processors (4th, 5th)                                                         |
| **Validated Software** | Ubuntu 22.04                                                                           |
|                        | Habana v1.21 ([link](https://docs.habana.ai/en/v1.21.2/Installation_Guide/index.html)) |
|                        | Docker version 28.3.3                                                                  |
|                        | Docker Compose version v2.39.1                                                         |
|                        | Kubernetes v1.32.7                                                                     |
|                        | HabanaAI vLLM v0.6.6.post1+Gaudi-1.20.0                                                |
|                        | vLLM v1.10.0                                                                           |
|                        | TGI v2.4.0 (Xeon), v2.3.1 (Gaudi), v2.4.1 (ROCm)                                       |
|                        | TEI v1.7                                                                               |
