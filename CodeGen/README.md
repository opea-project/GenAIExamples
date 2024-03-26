Code generation is a noteworthy application of Large Language Model (LLM) technology. In this example, we present a Copilot application to showcase how code generation can be executed on the Intel Gaudi2 platform. This CodeGen use case involves code generation utilizing open source models such as "m-a-p/OpenCodeInterpreter-DS-6.7B", "deepseek-ai/deepseek-coder-33b-instruct" and Text Generation Inference on Intel Gaudi2.


# Environment Setup
To use [🤗 text-generation-inference](https://github.com/huggingface/text-generation-inference) on Intel Gaudi2, please follow these steps:

## Prepare Gaudi Image
Getting started is straightforward with the official Docker container. Simply pull the image using:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

Alternatively, you can build the Docker image yourself with:

```bash
bash ./tgi_gaudi/build_docker.sh
```

## Launch TGI Gaudi Service

### Launch a local server instance on 1 Gaudi card:
```bash
bash ./tgi_gaudi/launch_tgi_service.sh
```

### Launch a local server instance on 4 Gaudi cards:
```bash
bash ./tgi_gaudi/launch_tgi_service.sh 4 9000 "deepseek-ai/deepseek-coder-33b-instruct"
```

### Customize TGI Gaudi Service

The ./tgi_gaudi/launch_tgi_service.sh script accepts three parameters:
- num_cards: The number of Gaudi cards to be utilized, ranging from 1 to 8. The default is set to 1.
- port_number: The port number assigned to the TGI Gaudi endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "m-a-p/OpenCodeInterpreter-DS-6.7B".

You have the flexibility to customize these parameters according to your specific needs. Additionally, you can set the TGI Gaudi endpoint by exporting the environment variable `TGI_ENDPOINT`:
```bash
export TGI_ENDPOINT="xxx.xxx.xxx.xxx:8080"
```

## Launch Copilot Docker

### Build Copilot Docker Image (Optional)

```bash
cd codegen
bash ./build_docker.sh
cd ..
```

### Lanuch Copilot Docker

```bash
docker run -it -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} --net=host --ipc=host -v /var/run/docker.sock:/var/run/docker.sock intel/gen-ai-examples:copilot bash
```

# Start Copilot Server

## Start the Backend Service
Make sure TGI-Gaudi service is running and also make sure data is populated into Redis. Launch the backend service:

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token ans export `HUGGINGFACEHUB_API_TOKEN` environment with the token.


```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
nohup python server.py &
```


## Install Copilot VSCode extension offline

Copy the vsix file `copilot-0.0.1.vsix` to local and install it in VSCode as below.

![Install-screenshot](https://i.imgur.com/JXQ3rqE.jpg)

We will be also releasing the plugin in Visual Studio Code plugin market to facilitate the installation.

# How to use

## Service URL setting

Please adjust the service URL in the extension settings based on the endpoint of the code generation backend service.

![Setting-screenshot](https://i.imgur.com/4hjvKPu.png)
![Setting-screenshot](https://i.imgur.com/JfJVFV3.png)

## Customize

The Copilot enables users to input their corresponding sensitive information and tokens in the user settings according to their own needs. This customization enhances the accuracy and output content to better meet individual requirements.

![Customize](https://i.imgur.com/PkObak9.png)

## Code suggestion

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
