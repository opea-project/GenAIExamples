# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain_core.prompts import ChatPromptTemplate

DOC_GRADER_PROMPT = """\
Given the QUERY, determine if the DOCUMENT contains all the information to answer the query.\n
QUERY: {question} \n
DOCUMENT:\n{context}\n\n
Give score 'yes' if the document provides all the information needed to answer the question. Otherwise, give score 'no'. ONLY answer with 'yes' or 'no'. NOTHING ELSE."""


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


QueryWriterLlamaPrompt = """\
Given the user question, think step by step.
If you can answer the question without searching the knowledge base, provide your answer.

If you need to search for information in the knowledge base, provide the search query.
Decompose a complex question into a set of simple tasks, and issue search queries for each task.
Here is the history of search queries that you have issued.
{history}
Here are the feedback for the documents retrieved with your search queries.
{feedback}

What is the new query that you should issue to the knowledge base to answer the user question?
Output the new query in JSON format as below.
{{"query": "your new query here"}}
If you plan to issue multiple queries, you must output JSON in multiple lines like the example below.
{{"query": "your first query here"}}
{{"query": "your second query here"}}

If you can directly answer the user question, output your answer in JSON format as below.
{{"answer": "your answer here"}}

User Question: {question}
You Output:\n
"""
