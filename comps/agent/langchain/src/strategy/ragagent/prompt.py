# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

DOC_GRADER_PROMPT = """\
Given the QUERY, determine if a relevant answer can be derived from the DOCUMENT.\n
QUERY: {question} \n
DOCUMENT:\n{context}\n\n
Give score 'yes' if the document provides sufficient and relevant information to answer the question. Otherwise, give score 'no'. ONLY answer with 'yes' or 'no'. NOTHING ELSE."""


PROMPT = """\
### You are a helpful, respectful and honest assistant.
You are given a Question and the time when it was asked in the Pacific Time Zone (PT), referred to as "Query
Time". The query time is formatted as "mm/dd/yyyy, hh:mm:ss PT".
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Refer to the search results to form your answer.
4. Give concise, factual and relevant answers.

### Search results: {context} \n
### Question: {question} \n
### Query Time: {time} \n
### Answer:
"""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            PROMPT,
        ),
    ]
)
