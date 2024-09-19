# FaqGen Evaluation

## Dataset

We evaluate performance on QA dataset [Squad_v2](https://huggingface.co/datasets/rajpurkar/squad_v2). Generate FAQs on "context" columns in validation dataset, which contains 1204 unique records.

First download dataset and put at "./data".

Extract unique "context" columns, which will be save to 'data/sqv2_context.json':

```
python get_context.py
```

## Generate FAQs

### Launch FaQGen microservice

Please refer to [FaQGen microservice](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/faq-generation/tgi), set up an microservice endpoint.

```
export FAQ_ENDPOINT = "http://${your_ip}:9000/v1/faqgen"
```

### Generate FAQs with microservice

Use the microservice endpoint to generate FAQs for dataset.

```
python generate_FAQ.py
```

Post-process the output to get the right data, which will be save to 'data/sqv2_faq.json'.

```
python post_process_FAQ.py
```

## Evaluate with Ragas

### Launch TGI service

We use "mistralai/Mixtral-8x7B-Instruct-v0.1" as LLM referee to evaluate the model. First we need to launch a LLM endpoint on Gaudi.

```
export HUGGING_FACE_HUB_TOKEN="your_huggingface_token"
bash launch_tgi.sh
```

Get the endpoint:

```
export LLM_ENDPOINT = "http://${ip_address}:8082"
```

Verify the service:

```bash
curl http://${ip_address}:8082/generate \
    -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":128}}' \
    -H 'Content-Type: application/json'
```

### Evaluate

evaluate the performance with the LLM:

```
python evaluate.py
```

### Performance Result

Here is the tested result for your reference
| answer_relevancy | faithfulness | context_utilization | reference_free_rubrics_score |
| ---- | ---- |---- |---- |
| 0.7191 | 0.9681 | 0.8964 | 4.4125|
