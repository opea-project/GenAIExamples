from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Redis
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_community.llms import HuggingFaceEndpoint
from langchain.callbacks import streaming_stdout
import intel_extension_for_pytorch as ipex
import torch

from rag_redis.config import (
    EMBED_MODEL,
    INDEX_NAME,
    INDEX_SCHEMA,
    REDIS_URL,
    TGI_ENDPOINT_NO_RAG,
)

# Make this look better in the docs.
class Question(BaseModel):
    __root__: str


# Define our prompt
template = """
Answer the question

---------
Question: {question}
---------

Answer:
"""

prompt = ChatPromptTemplate.from_template(template)

# RAG Chain
callbacks = [streaming_stdout.StreamingStdOutCallbackHandler()]
model = HuggingFaceEndpoint(
    endpoint_url=TGI_ENDPOINT_NO_RAG,
    max_new_tokens=512,
    top_k=10,
    top_p=0.95,
    typical_p=0.95,
    temperature=0.01,
    repetition_penalty=1.03,
    streaming=True,
    truncate=1024
)

chain = (
    RunnableParallel({"question": RunnablePassthrough()})
    | prompt
    | model
    | StrOutputParser()
).with_types(input_type=Question)
