# Finance Agent
## 1. Overview


## 2. Getting started
### 2.1 Dowload repos
```bash
mkdir /path/to/your/workspace/
export WORKDIR=/path/to/your/workspace/
genaicomps
genaiexamples
```
### 2.2 Set up env vars
```bash
export HF_CACHE_DIR=/path/to/your/model/cache/
export HF_TOKEN=<you-hf-token>

```

### 2.3 Build docker images
Build docker images for dataprep, agent, agent-ui.
```bash
# use docker image build
```

If deploy on Gaudi, also need to build vllm image.
```bash
cd $WORKDIR
git clone https://github.com/HabanaAI/vllm-fork.git
# get the latest release tag of vllm gaudi
cd vllm-fork
VLLM_VER=$(git describe --tags "$(git rev-list --tags --max-count=1)")
echo "Check out vLLM tag ${VLLM_VER}"
git checkout ${VLLM_VER}
docker build --no-cache -f Dockerfile.hpu -t opea/vllm-gaudi:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
```

## 3. Deploy with docker compose
### 3.1 Launch vllm endpoint
Below is the command to launch a vllm endpoint on Gaudi that serves `meta-llama/Llama-3.3-70B-Instruct` model on 4 Gaudi cards.
```bash
export vllm_port=8086
export vllm_volume=$HF_CACHE_DIR
export max_length=16384
export model="meta-llama/Llama-3.3-70B-Instruct"
docker run -d --runtime=habana --rm --name "vllm-gaudi-server" -e HABANA_VISIBLE_DEVICES=all -p $vllm_port:8000 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host opea/vllm-gaudi:comps --model ${model} --max-seq-len-to-capture $max_length --tensor-parallel-size 4
```
### 3.2 Prepare knowledge base
The commands below will upload some example files into the knowledge base. You can also upload files through UI.

First, launch the redis databases and the dataprep microservice.
```bash
docker compose -f $WORKDIR/GenAIExamples/FinanceAgent/docker_compose/intel/hpu/gaudi/dataprep_compose.yaml up -d
```

### 3.3 Launch the multi-agent system
### 3.4 Validate agents

