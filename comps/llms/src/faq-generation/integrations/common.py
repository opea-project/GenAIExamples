# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0

import os

import requests
from fastapi.responses import StreamingResponse
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import PromptTemplate

from comps import CustomLogger, GeneratedDoc, LLMParamsDoc, OpeaComponent, ServiceType
from comps.cores.mega.utils import ConfigError, get_access_token, load_model_configs

logger = CustomLogger("opea_faqgen")
logflag = os.getenv("LOGFLAG", False)

templ = """Create a concise FAQs (frequently asked questions and answers) for following text:
            TEXT: {text}
            Do not use any prefix or suffix to the FAQ.
        """

# Environment variables
MODEL_NAME = os.getenv("LLM_MODEL_ID")
MODEL_CONFIGS = os.getenv("MODEL_CONFIGS")
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

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


class OPEAFAQGen(OpeaComponent):
    """A specialized OPEA FAQGen component derived from OpeaComponent.

    Attributes:
        client (TGI/vLLM): An instance of the TGI/vLLM client for text generation.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LLM.name.lower(), description, config)
        self.access_token = (
            get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
        )
        self.text_splitter = CharacterTextSplitter()
        self.llm_endpoint = get_llm_endpoint()
        health_status = self.check_health()
        if not health_status:
            logger.error("OPEAFAQGen health check failed.")

    async def generate(self, input: LLMParamsDoc, client):
        """Invokes the TGI/vLLM LLM service to generate FAQ output for the provided input.

        Args:
            input (LLMParamsDoc): The input text(s).
            client: TGI/vLLM based client
        """
        PROMPT = PromptTemplate.from_template(templ)
        llm_chain = load_summarize_chain(llm=client, prompt=PROMPT)
        texts = self.text_splitter.split_text(input.query)

        # Create multiple documents
        docs = [Document(page_content=t) for t in texts]

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
            response = response["output_text"]
            if logflag:
                logger.info(response)
            return GeneratedDoc(text=response, prompt=input.query)
