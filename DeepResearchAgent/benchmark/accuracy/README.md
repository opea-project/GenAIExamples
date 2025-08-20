# Deep Research Agent Benchmarks

## Deploy the Deep Research Agent

Follow the doc [here](https://github.com/opea-project/GenAIExamples/tree/main/DeepResearchAgent) to setup deep research agent service.

## Evaluation

```
python eval.py --datasets together-search-bench --limit 1
```

The default values for arguments are:

| Argument       | Default value                                | Description                                                                                         |
| -------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| --datasets     | together-search-bench                        | benchmark datasets, supports "smolagents:simpleqa", "hotpotqa", "simpleqa", "together-search-bench" |
| --service-url  | http://localhost:8022/v1/deep_research_agent | the deep research agent endpoint                                                                    |
| --llm-endpoint | http://localhost:8000/v1/                    | the llm endpoint, like vllm, for llm as judge                                                       |
| --model        | openai/meta-llama/Llama-3.3-70B-Instruct     | the model id served by vllm, the prefix openai is the format of litellm                             |

## Accuracy

We randomly select 30 samples from the dataset [togethercomputer/together-search-bench](https://huggingface.co/datasets/togethercomputer/together-search-bench) randomly and compare the results of base model and deep research agent. The results show deep research agent can improve the generation quality and accuracy.

| model                                                                                                                  | accuracy |
| ---------------------------------------------------------------------------------------------------------------------- | -------- |
| [meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)                          | 0.433333 |
| deep research agent with [meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) | 0.8      |
