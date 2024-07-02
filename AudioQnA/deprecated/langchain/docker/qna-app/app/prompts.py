#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ========= Raw Q&A template prompt =========
template = """### System:\n\n
    You are an assistant chatbot. You answer questions. \
    If you don't know the answer, just say that you don't know. \
    Use three sentences maximum and keep the answer concise.\
### User:\n{question}\n### Assistant:\n"""
prompt = ChatPromptTemplate.from_template(template)


# ========= contextualize prompt =========
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)


# ========= Q&A with history prompt =========
# qa_system_prompt = """You are an assistant for question-answering tasks. \
# Use the following pieces of retrieved context to answer the question. \
# If you don't know the answer, just say that you don't know. \
# Use three sentences maximum and keep the answer concise.\

# {context}"""
# qa_prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", qa_system_prompt),
#         MessagesPlaceholder(variable_name="chat_history"),
#         ("human", "{question}"),
#     ]
# )
template = """### System:\n\n
    You are an assistant chatbot. You answer questions. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.\
{context}
### User:\n{question}\n### Assistant:\n"""
qa_prompt = ChatPromptTemplate.from_template(template)
