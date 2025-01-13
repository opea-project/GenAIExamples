# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests
from fastapi.responses import StreamingResponse
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from transformers import AutoTokenizer

from comps import CustomLogger, DocSumLLMParams, GeneratedDoc, OpeaComponent, ServiceType
from comps.cores.mega.utils import ConfigError, get_access_token, load_model_configs

from .template import templ_en, templ_refine_en, templ_refine_zh, templ_zh

logger = CustomLogger("llm_docsum")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
MODEL_NAME = os.getenv("LLM_MODEL_ID")
MODEL_CONFIGS = os.getenv("MODEL_CONFIGS")
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", 2048))
MAX_TOTAL_TOKENS = int(os.getenv("MAX_TOTAL_TOKENS", 4096))

if os.getenv("LLM_ENDPOINT") is not None:
    DEFAULT_ENDPOINT = os.getenv("LLM_ENDPOINT")
elif os.getenv("TGI_LLM_ENDPOINT") is not None:
    DEFAULT_ENDPOINT = os.getenv("TGI_LLM_ENDPOINT")
elif os.getenv("vLLM_ENDPOINT") is not None:
    DEFAULT_ENDPOINT = os.getenv("vLLM_ENDPOINT")
else:
    DEFAULT_ENDPOINT = "http://localhost:8080"


def get_llm_endpoint():
    if not MODEL_CONFIGS:
        return DEFAULT_ENDPOINT
    else:
        # Validate and Load the models config if MODEL_CONFIGS is not null
        configs_map = {}
        try:
            configs_map = load_model_configs(MODEL_CONFIGS)
        except ConfigError as e:
            logger.error(f"Failed to load model configurations: {e}")
            raise ConfigError(f"Failed to load model configurations: {e}")
        try:
            return configs_map.get(MODEL_NAME).get("endpoint")
        except ConfigError as e:
            logger.error(f"Input model {MODEL_NAME} not present in model_configs. Error {e}")
            raise ConfigError(f"Input model {MODEL_NAME} not present in model_configs")


class OPEADocSum(OpeaComponent):
    """A specialized OPEA DocSum component derived from OpeaComponent.

    Attributes:
        client (TGI/vLLM): An instance of the TGI/vLLM client for text generation.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LLM.name.lower(), description, config)
        self.access_token = (
            get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
        )
        self.llm_endpoint = get_llm_endpoint()
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        health_status = self.check_health()
        if not health_status:
            logger.error("OPEADocSum health check failed.")

    async def generate(self, input: DocSumLLMParams, client):
        """Invokes the TGI/vLLM LLM service to generate summarization for the provided input.

        Args:
            input (DocSumLLMParams): The input text(s).
            client: TGI/vLLM based client
        """
        ### check summary type
        summary_types = ["auto", "stuff", "truncate", "map_reduce", "refine"]
        if input.summary_type not in summary_types:
            raise NotImplementedError(f"Please specify the summary_type in {summary_types}")
        if input.summary_type == "auto":  ### Check input token length in auto mode
            token_len = len(self.tokenizer.encode(input.query))
            if token_len > MAX_INPUT_TOKENS + 50:
                input.summary_type = "refine"
                if logflag:
                    logger.info(
                        f"Input token length {token_len} exceed MAX_INPUT_TOKENS + 50 {MAX_INPUT_TOKENS+50}, auto switch to 'refine' mode."
                    )
            else:
                input.summary_type = "stuff"
                if logflag:
                    logger.info(
                        f"Input token length {token_len} not exceed MAX_INPUT_TOKENS + 50 {MAX_INPUT_TOKENS+50}, auto switch to 'stuff' mode."
                    )

        ### Check input language
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
        else:
            if input.summary_type == "refine":
                if MAX_TOTAL_TOKENS <= 2 * input.max_tokens + 128:  ## 128 is reserved prompt length
                    raise RuntimeError("In Refine mode, Please set MAX_TOTAL_TOKENS larger than (max_tokens * 2 + 128)")
                max_input_tokens = min(MAX_TOTAL_TOKENS - 2 * input.max_tokens - 128, MAX_INPUT_TOKENS)
            else:
                if MAX_TOTAL_TOKENS <= input.max_tokens + 50:  # 50 is reserved token length for prompt
                    raise RuntimeError("Please set MAX_TOTAL_TOKENS larger than max_tokens + 50)")
                max_input_tokens = min(MAX_TOTAL_TOKENS - input.max_tokens - 50, MAX_INPUT_TOKENS)
            chunk_size = min(input.chunk_size, max_input_tokens) if input.chunk_size > 0 else max_input_tokens
            chunk_overlap = input.chunk_overlap if input.chunk_overlap > 0 else int(0.1 * chunk_size)
            text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
                tokenizer=self.tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            if logflag:
                logger.info(f"set chunk size to: {chunk_size}")
                logger.info(f"set chunk overlap to: {chunk_overlap}")

        texts = text_splitter.split_text(input.query)
        docs = [Document(page_content=t) for t in texts]
        if logflag:
            logger.info(f"Split input query into {len(docs)} chunks")
            logger.info(f"The character length of the first chunk is {len(texts[0])}")

        ## LLM chain
        summary_type = input.summary_type
        if summary_type == "stuff":
            llm_chain = load_summarize_chain(llm=client, prompt=PROMPT)
        elif summary_type == "truncate":
            docs = [docs[0]]
            llm_chain = load_summarize_chain(llm=client, prompt=PROMPT)
        elif summary_type == "map_reduce":
            llm_chain = load_summarize_chain(
                llm=client,
                map_prompt=PROMPT,
                combine_prompt=PROMPT,
                chain_type="map_reduce",
                return_intermediate_steps=True,
            )
        elif summary_type == "refine":
            llm_chain = load_summarize_chain(
                llm=client,
                question_prompt=PROMPT,
                refine_prompt=PROMPT_REFINE,
                chain_type="refine",
                return_intermediate_steps=True,
            )
        else:
            raise NotImplementedError(f"Please specify the summary_type in {summary_types}")

        if input.stream:

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
