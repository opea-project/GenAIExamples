# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import re


class ChatTemplate:
    @staticmethod
    def generate_rag_prompt(question, documents):
        context_str = "\n".join(documents)
        if context_str and len(re.findall("[\u4E00-\u9FFF]", context_str)) / len(context_str) >= 0.3:
            # chinese context
            template = """
### 你将扮演一个乐于助人、尊重他人并诚实的助手，你的目标是帮助用户解答问题。有效地利用来自本地知识库的搜索结果。确保你的回答中只包含相关信息。如果你不确定问题的答案，请避免分享不准确的信息。
### 搜索结果：{context}
### 问题：{question}
### 回答：
"""
        else:
            template = """
### You are a helpful, respectful and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate the information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \n
### Search results: {context} \n
### Question: {question} \n
### Answer:
"""
        return template.format(context=context_str, question=question)


input_sentences = [
    "DeepSpeed is a machine learning framework",
    "He is working on",
    "He has a",
    "He got all",
    "Everyone is happy and I can",
    "The new movie that got Oscar this year",
    "In the far far distance from our galaxy,",
    "Peace is the only way",
]


llm_model = os.getenv("LLM_NATIVE_MODEL", "Qwen/Qwen2-7B-Instruct")
args_dict = {
    "device": "hpu",
    "model_name_or_path": llm_model,
    "bf16": True,
    "max_new_tokens": 100,
    "max_input_tokens": 0,
    "batch_size": 1,
    "warmup": 3,
    "n_iterations": 5,
    "local_rank": 0,
    "use_kv_cache": True,
    "use_hpu_graphs": True,
    "dataset_name": None,
    "column_name": None,
    "do_sample": False,
    "num_beams": 1,
    "trim_logits": False,
    "seed": 27,
    "profiling_warmup_steps": 0,
    "profiling_steps": 0,
    "profiling_record_shapes": False,
    "prompt": None,
    "bad_words": None,
    "force_words": None,
    "assistant_model": None,
    "peft_model": None,
    "num_return_sequences": 1,
    "token": None,
    "model_revision": "main",
    "attn_softmax_bf16": False,
    "output_dir": None,
    "bucket_size": -1,
    "bucket_internal": False,
    "dataset_max_samples": -1,
    "limit_hpu_graphs": False,
    "reuse_cache": False,
    "verbose_workers": False,
    "simulate_dyn_prompt": None,
    "reduce_recompile": False,
    "use_flash_attention": False,
    "flash_attention_recompute": False,
    "flash_attention_causal_mask": False,
    "flash_attention_fast_softmax": False,
    "book_source": False,
    "torch_compile": False,
    "ignore_eos": True,
    "temperature": 1.0,
    "top_p": 1.0,
    "const_serialization_path": None,
    "disk_offload": False,
    "trust_remote_code": False,
    "quant_config": "",
    "world_size": 0,
}
