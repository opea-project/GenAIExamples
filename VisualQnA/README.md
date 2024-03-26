# Visual Question and Answering

This example guides you through how to deploy a [LLaVA](https://llava-vl.github.io/) (Large Language and Vision Assistant) model on Intel Gaudi2 to do visual question and answering task. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products/) for more details.


![llava screenshot](https://i.imgur.com/Sqmoql8.png)
![llava-screenshot](https://i.imgur.com/4wETEe7.png)

## Start the LLaVA service

1. Build the Docker image needed for starting the service

```
cd serving/
docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy} -t intel/gen-ai-examples:llava-gaudi
```

2. Start the LLaVA service on Intel Gaudi2

```
docker run -d -p 8084:80 -p 8085:8000 -v ./data:/root/.cache/huggingface/hub/ -e http_proxy=$http_proxy -e https_proxy=$http_proxy -v $PWD/llava_server:/llava_server --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host intel/gen-ai-examples:llava-gaudi
```

Here are some explanation about the above parameters:
* `-p 8085:8000`: This will map the 8000 port of the LLaVA service inside the container to the 8085 port on the host
* `-v ./data:/root/.cache/huggingface/hub/`: This is to prevent from re-downloading model files
* `http_proxy` and `https_proxy` are used if you have some proxy setting
* `--runtime=habana ...` is required for running this service on Intel Gaudi2

Now you have a LLaVa service with the exposed port `8085` and you can check whether this service is up by:

```
curl localhost:8085/health -v
```

If the reply has a `200 OK`, then the service is up.

## Start the Gradio app

Now you can start the frontend UI by following commands:

```
cd ui/
pip install -r requirements.txt
python app.py --host 0.0.0.0 --port 7860 --worker-addr http://localhost:8085 --share
```
Here are some explanation about the above parameters:

* `--host`: the host of the gradio app
* `--port`: the port of the gradio app, by default 7860
* `--worker-addr`: the LLaVA service IP address. If you setup the service on a different machine, please replace `localhost` to the IP address of your Gaudi2 host machine