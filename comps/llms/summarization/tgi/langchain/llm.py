# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.responses import StreamingResponse
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

from comps import CustomLogger, DocSumLLMParams, GeneratedDoc, ServiceType, opea_microservices, register_microservice
from comps.cores.mega.utils import get_access_token

logger = CustomLogger("llm_docsum")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", 2048))
MAX_TOTAL_TOKENS = int(os.getenv("MAX_TOTAL_TOKENS", 4096))
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "Intel/neural-chat-7b-v3-3")

templ_en = """Write a concise summary of the following:


"{text}"


CONCISE SUMMARY:"""

templ_zh = """请简要概括以下内容:


"{text}"


概况:"""


templ_refine_en = """\
Your job is to produce a final summary.
We have provided an existing summary up to a certain point: {existing_answer}
We have the opportunity to refine the existing summary (only if needed) with some more context below.
------------
{text}
------------
Given the new context, refine the original summary.
If the context isn't useful, return the original summary.\
"""

templ_refine_zh = """\
你的任务是生成一个最终摘要。
我们已经提供了部分摘要：{existing_answer}
如果有需要的话，可以通过以下更多上下文来完善现有摘要。
------------
{text}
------------
根据新上下文，完善原始摘要。
如果上下文无用，则返回原始摘要。\
"""


@register_microservice(
    name="opea_service@llm_docsum",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/docsum",
    host="0.0.0.0",
    port=9000,
)
async def llm_generate(input: DocSumLLMParams):
    if logflag:
        logger.info(input)

    if input.language in ["en", "auto"]:
        templ = templ_en
        templ_refine = templ_refine_en
    elif input.language in ["zh"]:
        templ = templ_zh
        templ_refine = templ_refine_zh
    else:
        raise NotImplementedError('Please specify the input language in "en", "zh", "auto"')

    ## Prompt
    PROMPT = PromptTemplate.from_template(templ)
    if input.summary_type == "refine":
        PROMPT_REFINE = PromptTemplate.from_template(templ_refine)
    if logflag:
        logger.info("After prompting:")
        logger.info(PROMPT)
        if input.summary_type == "refine":
            logger.info(PROMPT_REFINE)

    ## Split text
    if input.summary_type == "stuff":
        text_splitter = CharacterTextSplitter()
    elif input.summary_type in ["truncate", "map_reduce", "refine"]:
        if input.summary_type == "refine":
            if MAX_TOTAL_TOKENS <= 2 * input.max_tokens + 128:
                raise RuntimeError("In Refine mode, Please set MAX_TOTAL_TOKENS larger than (max_tokens * 2 + 128)")
            max_input_tokens = min(
                MAX_TOTAL_TOKENS - 2 * input.max_tokens - 128, MAX_INPUT_TOKENS
            )  # 128 is reserved token length for prompt
        else:
            if MAX_TOTAL_TOKENS <= input.max_tokens + 50:
                raise RuntimeError("Please set MAX_TOTAL_TOKENS larger than max_tokens + 50)")
            max_input_tokens = min(
                MAX_TOTAL_TOKENS - input.max_tokens - 50, MAX_INPUT_TOKENS
            )  # 50 is reserved token length for prompt
        chunk_size = min(input.chunk_size, max_input_tokens) if input.chunk_size > 0 else max_input_tokens
        chunk_overlap = input.chunk_overlap if input.chunk_overlap > 0 else int(0.1 * chunk_size)
        text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        if logflag:
            logger.info(f"set chunk size to: {chunk_size}")
            logger.info(f"set chunk overlap to: {chunk_overlap}")
    else:
        raise NotImplementedError('Please specify the summary_type in "stuff", "truncate", "map_reduce", "refine"')
    texts = text_splitter.split_text(input.query)
    docs = [Document(page_content=t) for t in texts]
    if logflag:
        logger.info(f"Split input query into {len(docs)} chunks")
        logger.info(f"The character length of the first chunk is {len(texts[0])}")

    ## Access auth
    access_token = (
        get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
    )
    server_kwargs = {}
    if access_token:
        server_kwargs["headers"] = {"Authorization": f"Bearer {access_token}"}

    ## LLM
    if input.streaming and input.summary_type == "map_reduce":
        logger.info("Map Reduce mode don't support streaming=True, set to streaming=False")
        input.streaming = False
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint,
        max_new_tokens=input.max_tokens,
        top_k=input.top_k,
        top_p=input.top_p,
        typical_p=input.typical_p,
        temperature=input.temperature,
        repetition_penalty=input.repetition_penalty,
        streaming=input.streaming,
        server_kwargs=server_kwargs,
    )

    ## LLM chain
    summary_type = input.summary_type
    if summary_type == "stuff":
        llm_chain = load_summarize_chain(llm=llm, prompt=PROMPT)
    elif summary_type == "truncate":
        docs = [docs[0]]
        llm_chain = load_summarize_chain(llm=llm, prompt=PROMPT)
    elif summary_type == "map_reduce":
        llm_chain = load_summarize_chain(
            llm=llm, map_prompt=PROMPT, combine_prompt=PROMPT, chain_type="map_reduce", return_intermediate_steps=True
        )
    elif summary_type == "refine":
        llm_chain = load_summarize_chain(
            llm=llm,
            question_prompt=PROMPT,
            refine_prompt=PROMPT_REFINE,
            chain_type="refine",
            return_intermediate_steps=True,
        )
    else:
        raise NotImplementedError('Please specify the summary_type in "stuff", "truncate", "map_reduce", "refine"')

    if input.streaming:

        async def stream_generator():
            from langserve.serialization import WellKnownLCSerializer

            _serializer = WellKnownLCSerializer()
            async for chunk in llm_chain.astream_log(docs):
                data = _serializer.dumps({"ops": chunk.ops}).decode("utf-8")
                if logflag:
                    logger.info(data)
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        response = await llm_chain.ainvoke(docs)

        if input.summary_type in ["map_reduce", "refine"]:
            intermediate_steps = response["intermediate_steps"]
            if logflag:
                logger.info("intermediate_steps:")
                logger.info(intermediate_steps)

        output_text = response["output_text"]
        if logflag:
            logger.info("\n\noutput_text:")
            logger.info(output_text)

        return GeneratedDoc(text=output_text, prompt=input.query)


if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_ID)
    opea_microservices["opea_service@llm_docsum"].start()
