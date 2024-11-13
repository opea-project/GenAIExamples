# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.responses import StreamingResponse
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.llms import VLLMOpenAI

from comps import CustomLogger, GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice
from comps.cores.mega.utils import get_access_token

logger = CustomLogger("llm_docsum")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MODEL_ID = os.getenv("LLM_MODEL_ID", None)

templ_en = """Write a concise summary of the following:
"{text}"
CONCISE SUMMARY:"""

templ_zh = """请简要概括以下内容:
"{text}"
概况:"""


def post_process_text(text: str):
    if text == " ":
        return "data: @#$\n\n"
    if text == "\n":
        return "data: <br/>\n\n"
    if text.isspace():
        return None
    new_text = text.replace(" ", "@#$")
    return f"data: {new_text}\n\n"


@register_microservice(
    name="opea_service@llm_docsum",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/docsum",
    host="0.0.0.0",
    port=9000,
)
async def llm_generate(input: LLMParamsDoc):
    if logflag:
        logger.info(input)
    if input.language in ["en", "auto"]:
        templ = templ_en
    elif input.language in ["zh"]:
        templ = templ_zh
    else:
        raise NotImplementedError('Please specify the input language in "en", "zh", "auto"')

    PROMPT = PromptTemplate.from_template(templ)

    if logflag:
        logger.info("After prompting:")
        logger.info(PROMPT)

    access_token = (
        get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
    )
    headers = {}
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
    llm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8080")
    model = input.model if input.model else os.getenv("LLM_MODEL_ID")
    llm = VLLMOpenAI(
        openai_api_key="EMPTY",
        openai_api_base=llm_endpoint + "/v1",
        model_name=model,
        default_headers=headers,
        max_tokens=input.max_tokens,
        top_p=input.top_p,
        streaming=input.streaming,
        temperature=input.temperature,
        presence_penalty=input.repetition_penalty,
    )
    llm_chain = load_summarize_chain(llm=llm, prompt=PROMPT)
    texts = text_splitter.split_text(input.query)

    # Create multiple documents
    docs = [Document(page_content=t) for t in texts]

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
        response = response["output_text"]
        if logflag:
            logger.info(response)
        return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    # Split text
    text_splitter = CharacterTextSplitter()
    opea_microservices["opea_service@llm_docsum"].start()
