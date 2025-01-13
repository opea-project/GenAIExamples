# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

templ_en = """Write a concise summary of the following:


"{text}"


CONCISE SUMMARY:"""

templ_zh = """请简要概括以下内容:


"{text}"


概况:"""


templ_refine_en = """Your job is to produce a final summary.
We have provided an existing summary up to a certain point, then we will provide more context.
You need to refine the existing summary (only if needed) with new context and generate a final summary.


Existing Summary:
"{existing_answer}"



New Context:
"{text}"



Final Summary:

"""

templ_refine_zh = """\
你的任务是生成一个最终摘要。
我们已经处理好部分文本并生成初始摘要, 并提供了新的未处理文本
你需要根据新提供的文本，结合初始摘要，生成一个最终摘要。


初始摘要:
"{existing_answer}"



新的文本:
"{text}"



最终摘要:

"""
