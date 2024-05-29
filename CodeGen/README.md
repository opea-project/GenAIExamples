# Code Generation

Code-generating LLMs are specialized AI models designed for the task of generating computer code. Such models undergo training with datasets that encompass repositories, specialized documentation, programming code, relevant web content, and other related data. They possess a deep understanding of various programming languages, coding patterns, and software development concepts. Code LLMs are engineered to assist developers and programmers. When these LLMs are seamlessly integrated into the developer's Integrated Development Environment (IDE), they possess a comprehensive understanding of the coding context, which includes elements such as comments, function names, and variable names. This contextual awareness empowers them to provide more refined and contextually relevant coding suggestions.

Capabilities of LLMs in Coding:

- Code Generation: streamline coding through Code Generation, enabling non-programmers to describe tasks for code creation.
- Code Completion: accelerate coding by suggesting contextually relevant snippets as developers type.
- Code Translation and Modernization: translate and modernize code across multiple programming languages, aiding interoperability and updating legacy projects.
- Code summarization: extract key insights from codebases, improving readability and developer productivity.
- Code Refactoring: offer suggestions for code refactoring, enhancing code performance and efficiency.
- AI-Assisted Testing: assist in creating test cases, ensuring code robustness and accelerating development cycles.
- Error Detection and Debugging: detect errors in code and provide detailed descriptions and potential fixes, expediting debugging processes.

In this example, we present a Code Copilot application to showcase how code generation can be executed on the Intel Gaudi2 platform. This CodeGen use case involves code generation utilizing open source models such as "m-a-p/OpenCodeInterpreter-DS-6.7B", "deepseek-ai/deepseek-coder-33b-instruct" and Text Generation Inference on Intel Gaudi2.

CodeGen architecture shows below:

![architecture](https://i.imgur.com/G9ozwFX.png)

# Deploy CodeGen Service

The CodeGen service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.

## Deploy CodeGen on Gaudi

Refer to the [Gaudi Guide](./docker-composer/gaudi/README.md) for instructions on deploying CodeGen on Gaudi.

## Deploy CodeGen on Xeon

Refer to the [Xeon Guide](./docker-composer/xeon/README.md) for instructions on deploying CodeGen on Xeon.

## Deploy CodeGen into Kubernetes on Xeon & Gaudi

Refer to the [Kubernetes Guide](./kubernetes/manifests/README.md) for instructions on deploying CodeGen into Kubernetes on Xeon & Gaudi.
