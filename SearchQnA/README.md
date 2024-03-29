# Search Question and Answering

Search Question and Answering is the task of using Search Engine (e.g. Google Search) to improve the QA quality. Large language models have limitation on answering real-time information or specific details because they are limited to prior training data. A search engine can make up this advantage. By using a search engine, this SearchQnA service will firstly look up the relevant source web pages and feed them as context to the LLMs, so LLMs can use those context to compose answers more precisely.

# Start Backend Service

- Start the TGI service to deploy your LLM

```sh
cd serving/tgi_gaudi
bash build_docker.sh
bash launch_tgi_service.sh
```

- Start the SearchQnA application using Google Search

```sh
cd /home/sdp/sihanche/GenAIExamples/SearchQnA/langchain/docker
docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy}  -t intel/gen-ai-examples:searchqna-gaudi --no-cache
docker run -e TGI_ENDPOINT=<TGI ENDPOINT> -e GOOGLE_CSE_ID=<GOOGLE CSE ID> -e GOOGLE_API_KEY=<GOOGLE API KEY> -e HUGGINGFACEHUB_API_TOKEN=<HUGGINGFACE API TOKEN> -p 8080:8000 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -v $PWD/qna-app:/qna-app --runtime=habana -e HABANA_VISIBE_DEVILCES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host intel/gen-ai-examples:searchqna-gaudi
```

- Test

```sh
curl http://localhost:8085/v1/rag/web_search_chat_stream -X POST -d '{"query":"Give me some latest news?"}' -H 'Content-Type: application/json'
```

# Start Frontend GUI

Navigate to the "ui" folder and execute the following commands to start the frontend GUI:

```bash
cd ui
sudo apt-get install npm && \
    npm install -g n && \
    n stable && \
    hash -r && \
    npm install -g npm@latest
```

For CentOS, please use the following commands instead:

```bash
curl -sL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs
```

Update the `BACKEND_BASE_URL` environment variable in the `.env` file by replacing the IP address '127.0.0.1' with the actual IP address.

Run the following command to install the required dependencies:

```bash
npm install
```

Start the development server by executing the following command:

```bash
nohup npm run dev &
```

This will initiate the frontend service and launch the application.
