# Hallucination Detection Microservice

## Introduction

Hallucination in AI, particularly in large language models (LLMs), spans a wide range of issues that can impact reliability, trustworthiness, and utility of AI-generated content. The content could be plausible-sounding but factually incorrect, irrelevant, or entirely fabricated. This phenomenon occurs when the model generates outputs that are not grounded in the input context, training data, or real-world knowledge. While LLMs excel at generating coherent responses, hallucinations pose a critical challenge for applications that demand accuracy, reliability, and trustworthiness.

### Forms of Hallucination

- **Factual Errors**: The AI generates responses containing incorrect or fabricated facts. _Example_: Claiming a historical event occurred when it did not.

- **Logical Inconsistencies**: Outputs that fail to follow logical reasoning or contradict themselves. _Example_: Stating that a person is alive in one sentence and deceased in another.

- **Context Misalignment**: Responses that diverge from the input prompt or fail to address the intended context. _Example_: Providing irrelevant information or deviating from topic.

- **Fabricated References**: Creating citations, statistics, or other details that appear authentic but lack real-world grounding. _Example_: Inventing a study or paper that doesn't exist.

### Importance of Hallucination Detection

The Importance of hallucination detection cannot be overstated. Ensuring the factual correctness and contextual fidelity of AI-generated content is essential for:

- **Building Trust**: Reducing hallucinations foster user confidence in AI system.
- **Ensuring Compliance**: Meeting legal and ethical standards in regulated industries.
- **Enhancing Reliability**: Improving the overall robustness and performance of AI applications.

### Define the Scope of Our Hallucination Detection

Tackling the entire scope of hallucination is beyond our immediate scope. Training datasets inherently lag behind the question-and-answer needs due to their static nature. Also, Retrieval-Augmented Generation (RAG) is emerging as a preferred approach for LLMs, where model outputs are grounded in retrieved context to enhance accuracy and relevance and rely on integration of Document-Question-Answer triplets.

Therefore, we focus on detecting contextualized hallucinations with the following strategies:

- Using LLM-as-a-judge to evaluate hallucinations.
- Detect whether Context-Question-Answer triplet contains hallucinations.

## 🚀1. Start Microservice based on vLLM endpoint on Intel Gaudi Accelerator

### 1.1 Define Environment Variables

```bash
export your_ip=<your ip>
export port_number=9008
export HUGGINGFACEHUB_API_TOKEN=<token>
export vLLM_ENDPOINT="http://${your_ip}:${port_number}"
export LLM_MODEL="PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct"
```

For gated models such as `LLAMA-2`, you will have to pass the environment HUGGINGFACEHUB_API_TOKEN. Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

### 1.2 Launch vLLM Service on Gaudi Accelerator

#### Launch vLLM service on a single node

```bash
bash ./launch_vllm_service.sh ${port_number} ${LLM_MODEL} hpu 1
```

## 2. Set up Hallucination Microservice

Then we wrap the vLLM Service into Hallucination Microservice.

### 2.1 Build Docker

```bash
bash build_docker_hallucination_microservice.sh
```

### 2.2 Launch Hallucination Microservice

```bash
bash launch_hallucination_microservice.sh
```

## 🚀3. Get Status of Hallucination Microservice

```bash
docker container logs -f hallucination-detection
```

## 🚀4. Consume Guardrail Micorservice Post-LLM

Once microservice starts, users can use examples (bash or python) below to apply hallucination detection for LLM's response (Post-LLM)

**Bash:**

<span style="font-size:20px">_Case without Hallucination (Valid Output)_</span>

```bash
DOCUMENT=".......An important part of CDC’s role during a public health emergency is to develop a test for the pathogen and equip state and local public health labs with testing capacity. CDC developed an rRT-PCR test to diagnose COVID-19. As of the evening of March 17, 89 state and local public health labs in 50 states......"

QUESTION="What kind of test can diagnose COVID-19?"

ANSWER=" rRT-PCR test"

DATA='{"messages":[{"role": "user", "content": "Given the following QUESTION, DOCUMENT and ANSWER you must analyze the provided answer and determine whether it is faithful to the contents of the DOCUMENT. The ANSWER must not offer new information beyond the context provided in the DOCUMENT. The ANSWER also must not contradict information provided in the DOCUMENT. Output your final verdict by strictly following this format: \"PASS\" is the answer is faithful to the DOCUMENT and \"FAIL\" if the answer is not faithful to the DOCUMENT. Show your reasoning.\n\n--\nQUESTION (THIS DOES NOT COUNT AS BACKGROUND INFORMATION):\n{question}\n\n--\nDOCUMENT:\n{document}\n\n--\nANSWER:\n{answer}\n\n--\n\n Your output should be in JSON FORMAT with the keys \"REASONING\" and \"SCORE\":\n{{\"REASONING\": <your reasoning as bullet points>, \"SCORE\": <your final score>}}"}], "max_tokens":600,"model": "PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct" }'

DATA=$(echo $DATA | sed "s/{question}/$QUESTION/g; s/{document}/$DOCUMENT/g; s/{answer}/$ANSWER/g")

printf "$DATA"

curl http://localhost:9080/v1/hallucination_detection \
    -H 'Content-Type: application/json' \
    -d "$DATA"
```

Example Output:

```bash
{"REASONING": ['The CONTEXT mentions that the CDC developed an rRT-PCR test to diagnose COVID-19.', 'The CONTEXT does not describe what rRT-PCR stands for or how the test works.', 'The ANSWER simply states that the test is an rRT-PCR test.', 'The ANSWER does not provide additional information about the test, such as its full form or methodology.', 'Given the QUESTION about what kind of test can diagnose COVID-19, the ANSWER is faithful to the CONTEXT because it correctly identifies the type of test developed by the CDC, even though it lacks detailed explanation.'], "SCORE": PASS}
```

<span style="font-size:20px">_Case with Hallucination (Invalid or Inconsistent Output)_</span>

```bash
DOCUMENT="750 Seventh Avenue is a 615 ft (187m) tall Class-A office skyscraper in New York City. 101 Park Avenue is a 629 ft tall skyscraper in New York City, New York."

QUESTION=" 750 7th Avenue and 101 Park Avenue, are located in which city?"

ANSWER="750 7th Avenue and 101 Park Avenue are located in Albany, New York"

DATA='{"messages":[{"role": "user", "content": "Given the following QUESTION, DOCUMENT and ANSWER you must analyze the provided answer and determine whether it is faithful to the contents of the DOCUMENT. The ANSWER must not offer new information beyond the context provided in the DOCUMENT. The ANSWER also must not contradict information provided in the DOCUMENT. Output your final verdict by strictly following this format: \"PASS\" is the answer is faithful to the DOCUMENT and \"FAIL\" if the answer is not faithful to the DOCUMENT. Show your reasoning.\n\n--\nQUESTION (THIS DOES NOT COUNT AS BACKGROUND INFORMATION):\n{question}\n\n--\nDOCUMENT:\n{document}\n\n--\nANSWER:\n{answer}\n\n--\n\n Your output should be in JSON FORMAT with the keys \"REASONING\" and \"SCORE\":\n{{\"REASONING\": <your reasoning as bullet points>, \"SCORE\": <your final score>}}"}], "max_tokens":600,"model": "PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct" }'

DATA=$(echo $DATA | sed "s/{question}/$QUESTION/g; s/{document}/$DOCUMENT/g; s/{answer}/$ANSWER/g")

printf "$DATA"

curl http://localhost:9080/v1/hallucination_detection \
    -H 'Content-Type: application/json' \
    -d "$DATA"

```

Example Output:

```bash
{"REASONING": ['The CONTEXT specifies that 750 Seventh Avenue and 101 Park Avenue are located in New York City.', 'The ANSWER incorrectly states that these locations are in Albany, New York.', 'The QUESTION asks for the city where these addresses are located.', 'The correct answer should be New York City, not Albany.'], "SCORE": FAIL}
```

**Python Script:**

```python
import requests
import json

proxies = {"http": ""}
url = "http://localhost:9080/v1/hallucination_detection"
data = {
    "messages": [
        {
            "role": "user",
            "content": 'Given the following QUESTION, DOCUMENT and ANSWER you must analyze the provided answer and determine whether it is faithful to the contents of the DOCUMENT. The ANSWER must not offer new information beyond the context provided in the DOCUMENT. The ANSWER also must not contradict information provided in the DOCUMENT. Output your final verdict by strictly following this format: "PASS" is the answer is faithful to the DOCUMENT and "FAIL" if the answer is not faithful to the DOCUMENT. Show your reasoning.\n\n--\nQUESTION (THIS DOES NOT COUNT AS BACKGROUND INFORMATION):\n 750 7th Avenue and 101 Park Avenue, are located in which city?\n\n--\nDOCUMENT:\n750 Seventh Avenue is a 615 ft (187m) tall Class-A office skyscraper in New York City. 101 Park Avenue is a 629 ft tall skyscraper in New York City, New York.\n\n--\nANSWER:\n750 7th Avenue and 101 Park Avenue are located in Albany, New York\n\n--\n\n Your output should be in JSON FORMAT with the keys "REASONING" and "SCORE":\n{{"REASONING": <your reasoning as bullet points>, "SCORE": <your final score>}}',
        }
    ],
    "max_tokens": 600,
    "model": "PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct",
}

try:
    resp = requests.post(url=url, data=data, proxies=proxies)
    print(resp.json())
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
```
