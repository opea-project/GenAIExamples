# CodeGen accuracy Evaluation

## Evaluation Framework

We evaluate accuracy by [bigcode-evaluation-harness](https://github.com/bigcode-project/bigcode-evaluation-harness). It is a framework for the evaluation of code generation models.

## Evaluation FAQs

### Launch CodeGen microservice

Please refer to [CodeGen Examples](https://github.com/opea-project/GenAIExamples/tree/main/CodeGen), follow the guide to deploy CodeGen megeservice.

Use `curl` command to test codegen service and ensure that it has started properly

```bash
export CODEGEN_ENDPOINT = "http://${your_ip}:7778/v1/codegen"
curl $CODEGEN_ENDPOINT \
    -H "Content-Type: application/json" \
    -d '{"messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."}'

```

### Generation and Evaluation

For evaluating the models on coding tasks or specifically coding LLMs, we follow the [bigcode-evaluation-harness](https://github.com/bigcode-project/bigcode-evaluation-harness) and provide the command line usage and function call usage. [HumanEval](https://huggingface.co/datasets/openai_humaneval), [HumanEval+](https://huggingface.co/datasets/evalplus/humanevalplus), [InstructHumanEval](https://huggingface.co/datasets/codeparrot/instructhumaneval), [APPS](https://huggingface.co/datasets/codeparrot/apps), [MBPP](https://huggingface.co/datasets/mbpp), [MBPP+](https://huggingface.co/datasets/evalplus/mbppplus), and [DS-1000](https://github.com/HKUNLP/DS-1000/) for both completion (left-to-right) and insertion (FIM) mode are available.

#### command line usage

```shell
git clone https://github.com/opea-project/GenAIEval
cd GenAIEval
pip install -r requirements.txt
pip install -e .

cd evals/evaluation/bigcode_evaluation_harness/examples
python main.py --model Qwen/CodeQwen1.5-7B-Chat \
  --tasks humaneval \
  --codegen_url $CODEGEN_ENDPOINT \
  --max_length_generation 2048 \
  --batch_size 1  \
  --save_generations \
  --save_references \
  --allow_code_execution
```

**_Note:_** Currently, our framework is designed to execute tasks in full. To ensure the accuracy of results, we advise against using the 'limit' or 'limit_start' parameters to restrict the number of test samples.

### accuracy Result

Here is the tested result for your reference

```json
{
  "humaneval": {
    "pass@1": 0.7195121951219512
  },
  "config": {
    "prefix": "",
    "do_sample": true,
    "temperature": 0.2,
    "top_k": 0,
    "top_p": 0.95,
    "n_samples": 1,
    "eos": "<|endoftext|>",
    "seed": 0,
    "model": "Qwen/CodeQwen1.5-7B-Chat",
    "modeltype": "causal",
    "peft_model": null,
    "revision": null,
    "use_auth_token": false,
    "trust_remote_code": false,
    "tasks": "humaneval",
    "instruction_tokens": null,
    "batch_size": 1,
    "max_length_generation": 2048,
    "precision": "fp32",
    "load_in_8bit": false,
    "load_in_4bit": false,
    "left_padding": false,
    "limit": null,
    "limit_start": 0,
    "save_every_k_tasks": -1,
    "postprocess": true,
    "allow_code_execution": true,
    "generation_only": false,
    "load_generations_path": null,
    "load_data_path": null,
    "metric_output_path": "evaluation_results.json",
    "save_generations": true,
    "load_generations_intermediate_paths": null,
    "save_generations_path": "generations.json",
    "save_references": true,
    "save_references_path": "references.json",
    "prompt": "prompt",
    "max_memory_per_gpu": null,
    "check_references": false,
    "codegen_url": "http://192.168.123.104:31234/v1/codegen"
  }
}
```
