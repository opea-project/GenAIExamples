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

# Environment Setup

To use [🤗 text-generation-inference](https://github.com/huggingface/text-generation-inference) on Intel Gaudi2, please follow these steps:

## Prepare Gaudi Image

Getting started is straightforward with the official Docker container. Simply pull the image using:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

Alternatively, you can build the Docker image yourself with:

```bash
bash ./serving/tgi_gaudi/build_docker.sh
```

## Launch TGI Gaudi Service

### Launch a local server instance on 1 Gaudi card:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh
```

### Launch a local server instance on 4 Gaudi cards:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh 4 9000 "deepseek-ai/deepseek-coder-33b-instruct"
```

### Customize TGI Gaudi Service

The ./tgi_gaudi/launch_tgi_service.sh script accepts three parameters:

- num_cards: The number of Gaudi cards to be utilized, ranging from 1 to 8. The default is set to 1.
- port_number: The port number assigned to the TGI Gaudi endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "m-a-p/OpenCodeInterpreter-DS-6.7B".

You have the flexibility to customize these parameters according to your specific needs. Additionally, you can set the TGI Gaudi endpoint by exporting the environment variable `TGI_ENDPOINT`:

```bash
export TGI_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
```

## Launch Copilot Docker

### Build Copilot Docker Image (Optional)

```bash
cd codegen
bash ./build_docker.sh
cd ..
```

### Launch Copilot Docker

```bash
docker run -it -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} --net=host --ipc=host -v /var/run/docker.sock:/var/run/docker.sock intel/gen-ai-examples:copilot bash
```

# Start Copilot Server

## Start the Backend Service

Make sure TGI-Gaudi service is running and also make sure data is populated into Redis. Launch the backend service:

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HF_TOKEN` environment with the token.

```bash
export HF_TOKEN=<token>
nohup python server.py &
```

The Copilot backend defaults to listening on port 8000, but you can adjust the port number as needed.

# Install Copilot VSCode extension from Plugin Marketplace

Install `Neural Copilot` in VSCode as below.

![Install-screenshot](https://i.imgur.com/cnHRAdD.png)

# How to use

## Service URL setting

Please adjust the service URL in the extension settings based on the endpoint of the code generation backend service.

![Setting-screenshot](https://i.imgur.com/4hjvKPu.png)
![Setting-screenshot](https://i.imgur.com/AQZuzqd.png)

## Customize

The Copilot enables users to input their corresponding sensitive information and tokens in the user settings according to their own needs. This customization enhances the accuracy and output content to better meet individual requirements.

![Customize](https://i.imgur.com/PkObak9.png)

## Code Suggestion

To trigger inline completion, you'll need to type # {your keyword} (start with your programming language's comment keyword, like // in C++ and # in python). Make sure Inline Suggest is enabled from the VS Code Settings.
For example:

![code suggestion](https://i.imgur.com/sH5UoTO.png)

To provide programmers with a smooth experience, the Copilot supports multiple ways to trigger inline code suggestions. If you are interested in the details, they are summarized as follows:

- Generate code from single-line comments: The simplest way introduced before.
- Generate code from consecutive single-line comments:

![codegen from single-line comments](https://i.imgur.com/GZsQywX.png)

- Generate code from multi-line comments, which will not be triggered until there is at least one `space` outside the multi-line comment):

![codegen from multi-line comments](https://i.imgur.com/PzhiWrG.png)

- Automatically complete multi-line comments:

![auto complete](https://i.imgur.com/cJO3PQ0.jpg)

## Chat with AI assistant

You can start a conversation with the AI programming assistant by clicking on the robot icon in the plugin bar on the left:

![icon](https://i.imgur.com/f7rzfCQ.png)

Then you can see the conversation window on the left, where you can chat with AI assistant:

![dialog](https://i.imgur.com/aiYzU60.png)

There are 4 areas worth noting:

- Enter and submit your question
- Your previous questions
- Answers from AI assistant (Code will be highlighted properly according to the programming language it is written in, also support streaming output)
- Copy or replace code with one click (Note that you need to select the code in the editor first and then click "replace", otherwise the code will be inserted)

You can also select the code in the editor and ask AI assistant question about it.
For example:

- Select code

![select code](https://i.imgur.com/grvrtY6.png)

- Ask question and get answer

![qna](https://i.imgur.com/8Kdpld7.png)

#

SCRIPT USAGE NOTICE:  By downloading and using any script file included with the associated software package (such as files with .bat, .cmd, or .JS extensions, Docker files, or any other type of file that, when executed, automatically downloads and/or installs files onto your system) (the “Script File”), it is your obligation to review the Script File to understand what files (e.g.,  other software, AI models, AI Datasets) the Script File will download to your system (“Downloaded Files”). Furthermore, by downloading and using the Downloaded Files, even if they are installed through a silent install, you agree to any and all terms and conditions associated with such files, including but not limited to, license terms, notices, or disclaimers.
