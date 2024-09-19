# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os

from evals.metrics.ragas import RagasMetric
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

llm_endpoint = os.getenv("LLM_ENDPOINT", "http://0.0.0.0:8082")

f = open("data/sqv2_context.json", "r")
sqv2_context = json.load(f)

f = open("data/sqv2_faq.json", "r")
sqv2_faq = json.load(f)

templ = """Create a concise FAQs (frequently asked questions and answers) for following text:
        TEXT: {text}
        Do not use any prefix or suffix to the FAQ.
    """

number = 1204
question = []
answer = []
ground_truth = ["None"] * number
contexts = []
for i in range(number):
    inputs = sqv2_context[str(i)]
    inputs_faq = templ.format_map({"text": inputs})
    actual_output = sqv2_faq[str(i)]

    question.append(inputs_faq)
    answer.append(actual_output)
    contexts.append([inputs_faq])

embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en-v1.5")
metrics_faq = ["answer_relevancy", "faithfulness", "context_utilization", "reference_free_rubrics_score"]
metric = RagasMetric(threshold=0.5, model=llm_endpoint, embeddings=embeddings, metrics=metrics_faq)

test_case = {"question": question, "answer": answer, "ground_truth": ground_truth, "contexts": contexts}

metric.measure(test_case)
print(metric.score)
