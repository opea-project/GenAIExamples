# LM-Eval Microservice

This microservice, designed for [lm-eval](https://github.com/EleutherAI/lm-evaluation-harness), which can host a separate llm server to evaluate `lm-eval` tasks.

## CPU service

### build cpu docker

```
docker build -f Dockerfile.cpu -t opea/lm-eval:latest .

```

### start the server

- set the environments `MODEL`, `MODEL_ARGS`, `DEVICE` and start the server

```
docker run -p 9006:9006 --ipc=host  -e MODEL="hf" -e MODEL_ARGS="pretrained=Intel/neural-chat-7b-v3-3" -e DEVICE="cpu" opea/lm-eval:latest
```

### evaluate the model

- set `base_url` and `tokenizer`

```
git clone https://github.com/opea-project/GenAIEval
cd GenAIEval
pip install -e .

cd GenAIEval/evaluation/lm_evaluation_harness/examples

python main.py \
    --model genai-hf \
    --model_args "base_url=http://{your_ip}:9006,tokenizer=Intel/neural-chat-7b-v3-3" \
    --tasks  "lambada_openai" \
    --batch_size 2

```
