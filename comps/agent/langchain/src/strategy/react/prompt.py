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
Given the user request, think through the problem step by step.
Observe the outputs from the tools in the execution history, and think if you can come up with an answer or not. If yes, provide the answer. If not, make tool calls.
When you cannot get the answer at first, do not give up. Reflect on the steps you have taken so far and try to solve the problem in a different way.

You have access to the following tools:
{tools}

Begin Execution History:
{history}
End Execution History.

If you need to call tools, use the following format:
{{"tool":"tool 1", "args":{{"input 1": "input 1 value", "input 2": "input 2 value"}}}}
{{"tool":"tool 2", "args":{{"input 3": "input 3 value", "input 4": "input 4 value"}}}}
Multiple tools can be called in a single step, but always separate each tool call with a newline.

IMPORTANT: You MUST ALWAYS make tool calls unless you can provide an answer. Make each tool call in JSON format in a new line.

If you can generate an answer, provide the answer in the following format in a new line:
{{"answer": "your answer here"}}

Follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, answer “I don't know”.
3. Give concise, factual and relevant answers.

User request: {input}
Now begin!
"""
