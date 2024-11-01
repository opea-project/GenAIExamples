# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain_core.prompts import PromptTemplate

hwchase17_react_prompt = PromptTemplate.from_template(
    "Answer the following questions as best you can. You have access to the following tools:\n\n{tools}\n\nUse the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin!\n\nQuestion: {input}\nThought:{agent_scratchpad}"
)


REACT_SYS_MESSAGE = """\
Decompose the user request into a series of simple tasks when necessary and solve the problem step by step.
When you cannot get the answer at first, do not give up. Reflect on the info you have from the tools and try to solve the problem in a different way.
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Give concise, factual and relevant answers.
"""

REACT_AGENT_LLAMA_PROMPT = """\
You are tasked with answering user questions.
You have the following tools to gather information:
{tools}

**Procedure:**
1. Read the question carefully. Divide the question into sub-questions and conquer sub-questions one by one.
2. Read the execution history if any to understand the tools that have been called and the information that has been gathered.
3. Reason about the information gathered so far and decide if you can answer the question or if you need to call more tools.

**Output format:**
You should output your thought process. Finish thinking first. Output tool calls or your answer at the end.
When making tool calls, you should use the following format:
TOOL CALL: {{"tool": "tool1", "args": {{"arg1": "value1", "arg2": "value2", ...}}}}
TOOL CALL: {{"tool": "tool2", "args": {{"arg1": "value1", "arg2": "value2", ...}}}}

If you can answer the question, provide the answer in the following format:
FINAL ANSWER: {{"answer": "your answer here"}}

Follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, answer “I don't know”.
3. Give concise, factual and relevant answers.

**IMPORTANT:**
* Divide the question into sub-questions and conquer sub-questions one by one.
* Questions may be time sensitive. Pay attention to the time when the question was asked.
* You may need to combine information from multiple tools to answer the question.
* If you did not get the answer at first, do not give up. Reflect on the steps that you have taken and try a different way. Think out of the box. You hard work will be rewarded.
* Do not make up tool outputs.

======= Your task =======
Question: {input}

Execution History:
{history}
========================

Now take a deep breath and think step by step to solve the problem.
"""
