# Code Translation

Code translation is the process of converting code written in one programming language to another programming language while maintaining the same functionality. This process is also known as code conversion, source-to-source translation, or transpilation. Code translation is often performed when developers want to take advantage of new programming languages, improve code performance, or maintain legacy systems. Some common examples include translating code from Python to Java, or from JavaScript to TypeScript.

The workflow falls into the following architecture:

![architecture](https://i.imgur.com/ums0brC.png)

# Start Backend Service

1. Start the TGI service to deploy your LLM

```sh
cd serving/tgi_gaudi
bash build_docker.sh
bash launch_tgi_service.sh
```

`launch_tgi_service.sh` by default uses `8080` as the TGI service's port. Please replace it if there are any port conflicts.

2. Start the CodeTranslation service

```sh
cd langchain/docker
bash build_docker.sh
docker run -it --name code_trans_server --net=host --ipc=host -e TGI_ENDPOINT=${TGI ENDPOINT} -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACE_API_TOKEN} -e SERVER_PORT=8000 -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} intel/gen-ai-examples:code-translation bash
```

Here is the explanation of some of the above parameters:

- `TGI_ENDPOINT`: The endpoint of your TGI service, usually equal to `<ip of your machine>:<port of your TGI service>`.
- `HUGGINGFACEHUB_API_TOKEN`: Your HuggingFace hub API token, usually generated [here](https://huggingface.co/settings/tokens).
- `SERVER_PORT`: The port of the CodeTranslation service on the host.

3. Quick test

```sh
curl http://localhost:8000/v1/code_translation \
    -X POST \
    -d '{"language_from": "Python","language_to": "Java","source_code": "\ndef hello(name):\n    print(\"Hello, \" + name)\n"}' \
    -H 'Content-Type: application/json'
```
