# Code Translation Application

Code translation is the process of converting code written in one programming language to another programming language while maintaining the same functionality. This process is also known as code conversion, source-to-source translation, or transpilation. Code translation is often performed when developers want to take advantage of new programming languages, improve code performance, or maintain legacy systems. Some common examples include translating code from Python to Java, or from JavaScript to TypeScript.

The workflow falls into the following architecture:

![architecture](https://i.imgur.com/ums0brC.png)

This Code Translation use case uses Text Generation Inference on Intel Gaudi2 or Intel XEON Scalable Processors. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products) for more details.

# Deploy Code Translation Service

The Code Translation service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.

## Deploy Code Translation on Gaudi

Refer to the [Gaudi Guide](./docker-composer/gaudi/README.md) for instructions on deploying Code Translation on Gaudi.

## Deploy Code Translation on Xeon

Refer to the [Xeon Guide](./docker-composer/xeon/README.md) for instructions on deploying Code Translation on Xeon.
