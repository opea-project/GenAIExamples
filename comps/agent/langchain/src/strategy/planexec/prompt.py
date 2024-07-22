# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

wfh_react_agent_executor = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        ("placeholder", "{{messages}}"),
    ]
)

hwchase17_react_prompt = PromptTemplate.from_template(
    "Answer the following questions as best you can. You have access to the following tools:\n\n{tools}\n\nUse the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of [{tool_names}]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin!\n\nQuestion: {input}\nThought:{agent_scratchpad}"
)

plan_check_prompt = PromptTemplate(
    template="""You are a grader assessing if the task is relevant to the question.\n
    Here is the task: \n\n {context} \n\n
    Here is the user question: {question} \n
    If the question is a good executable task then grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the task is relevant to the question.""",
    input_variables=["context", "question"],
)

answer_check_prompt = PromptTemplate(
    template="""You are a grader assessing if the Response is a good answer.\n
    Here is the Response: \n\n User question is '{input}', the answer is '{response}' \n\n
    Give a binary score 'yes' or 'no' score to indicate whether the Response is a complete sentence.""",
    input_variables=["response", "input"],
)

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a chain-of-thoughts step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.""",
        ),
        ("placeholder", "{messages}"),
    ]
)

answer_make_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with Final Answer. \
You need to follow rules listed below: \
1. Response with a complete sentence. \
2. Reply with keyword: 'Response'. \

Your objective was this:
{input}

You have currently done the follow steps and information::
{past_steps}

"""
)

replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with Final Answer or additional step by step plan. \
If you can respond with Final Answer, then reply with keyword: 'Response'. \
If you need more steps, then reply with keyword: 'Plan'. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)
