#!/usr/bin/env python

# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import uuid
from operator import itemgetter
from typing import Any, List, Mapping, Optional, Sequence

from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable.passthrough import RunnableAssign
from langchain_benchmarks import clone_public_dataset, registry
from langchain_benchmarks.rag import get_eval_config
from langchain_community.embeddings import HuggingFaceEmbeddings, HuggingFaceHubEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain_community.vectorstores import Redis
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.prompt_values import ChatPromptValue
from langchain_openai import ChatOpenAI
from langsmith.client import Client
from transformers import AutoTokenizer, LlamaForCausalLM

# Parameters and settings
ENDPOINT_URL_GAUDI2 = "http://localhost:8000"
ENDPOINT_URL_VLLM = "http://localhost:8001/v1"
TEI_ENDPOINT = "http://localhost:8002"
LANG_CHAIN_DATASET = "<Dataset name to add>"
HF_MODEL_NAME = "<Model name to add>"
PROMPT_TOKENS_LEN = 214  # Magic number for prompt template tokens
MAX_INPUT_TOKENS = 1024
MAX_OUTPUT_TOKENS = 128

# Generate a unique run ID for this experiment
run_uid = uuid.uuid4().hex[:6]

tokenizer = None


def crop_tokens(prompt, max_len):
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs_cropped = inputs["input_ids"][0:, 0:max_len]
    prompt_cropped = tokenizer.batch_decode(
        inputs_cropped, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    return prompt_cropped


# After the retriever fetches documents, this
# function formats them in a string to present for the LLM
def format_docs(docs: Sequence[Document]) -> str:
    formatted_docs = []
    for i, doc in enumerate(docs):
        doc_string = (
            f"<document index='{i}'>\n"
            f"<source>{doc.metadata.get('source')}</source>\n"
            f"<doc_content>{doc.page_content[0:]}</doc_content>\n"
            "</document>"
        )
        # Truncate the retrieval data based on the max tokens required
        cropped = crop_tokens(doc_string, MAX_INPUT_TOKENS - PROMPT_TOKENS_LEN)

        formatted_docs.append(cropped)  # doc_string
    formatted_str = "\n".join(formatted_docs)
    return f"<documents>\n{formatted_str}\n</documents>"


def ingest_dataset(args, langchain_docs):
    clone_public_dataset(langchain_docs.dataset_id, dataset_name=langchain_docs.name)
    docs = list(langchain_docs.get_docs())
    embedder = HuggingFaceHubEmbeddings(model=args.embedding_endpoint_url)

    _ = Redis.from_texts(
        # appending this little bit can sometimes help with semantic retrieval
        # especially with multiple companies
        texts=[d.page_content for d in docs],
        metadatas=[d.metadata for d in docs],
        embedding=embedder,
        index_name=args.db_index,
        index_schema=args.db_schema,
        redis_url=args.db_url,
    )


def GetLangchainDataset(args):
    registry_retrieved = registry.filter(Type="RetrievalTask")
    langchain_docs = registry_retrieved[args.langchain_dataset]
    return langchain_docs


def buildchain(args):
    embedder = HuggingFaceHubEmbeddings(model=args.embedding_endpoint_url)
    vectorstore = Redis.from_existing_index(
        embedding=embedder, index_name=args.db_index, schema=args.db_schema, redis_url=args.db_url
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an AI assistant answering questions about LangChain."
                "\n{context}\n"
                "Respond solely based on the document content.",
            ),
            ("human", "{question}"),
        ]
    )

    llm = None
    match args.llm_service_api:
        case "tgi-gaudi":
            llm = HuggingFaceEndpoint(
                endpoint_url=args.llm_endpoint_url,
                max_new_tokens=MAX_OUTPUT_TOKENS,
                top_k=10,
                top_p=0.95,
                typical_p=0.95,
                temperature=1.0,
                repetition_penalty=1.03,
                streaming=False,
                truncate=1024,
            )
        case "vllm-openai":
            llm = ChatOpenAI(
                model=args.model_name,
                openai_api_key="EMPTY",
                openai_api_base=args.llm_endpoint_url,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=1.0,
                top_p=0.95,
                streaming=False,
                frequency_penalty=1.03,
            )

    response_generator = (prompt | llm | StrOutputParser()).with_config(
        run_name="GenerateResponse",
    )

    # This is the final response chain.
    # It fetches the "question" key from the input dict,
    # passes it to the retriever, then formats as a string.

    chain = (
        RunnableAssign(
            {"context": (itemgetter("question") | retriever | format_docs).with_config(run_name="FormatDocs")}
        )
        # The "RunnableAssign" above returns a dict with keys
        # question (from the original input) and
        # context: the string-formatted docs.
        # This is passed to the response_generator above
        | response_generator
    )
    return chain


def run_test(args, chain):
    client = Client()
    test_run = client.run_on_dataset(
        dataset_name=args.langchain_dataset,
        llm_or_chain_factory=chain,
        evaluation=None,
        project_name=f"{args.llm_service_api}-{args.model_name} op-{MAX_OUTPUT_TOKENS} cl-{args.concurrency} iter-{run_uid}",
        project_metadata={
            "index_method": "basic",
        },
        concurrency_level=args.concurrency,
        verbose=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--llm_endpoint_url",
        type=str,
        required=False,
        default=ENDPOINT_URL_GAUDI2,
        help="LLM Service Endpoint URL",
    )
    parser.add_argument(
        "-e",
        "--embedding_endpoint_url",
        type=str,
        default=TEI_ENDPOINT,
        required=False,
        help="Embedding Service Endpoint URL",
    )
    parser.add_argument("-m", "--model_name", type=str, default=HF_MODEL_NAME, required=False, help="Model Name")
    parser.add_argument("-ht", "--huggingface_token", type=str, required=True, help="Huggingface API token")
    parser.add_argument("-lt", "--langchain_token", type=str, required=True, help="langchain API token")
    parser.add_argument(
        "-d",
        "--langchain_dataset",
        type=str,
        required=True,
        help="langchain dataset name Refer: https://docs.smith.langchain.com/evaluation/quickstart ",
    )

    parser.add_argument("-c", "--concurrency", type=int, default=16, required=False, help="Concurrency Level")

    parser.add_argument(
        "-lm",
        "--llm_service_api",
        type=str,
        default="tgi-gaudi",
        required=False,
        help='Choose between "tgi-gaudi" or "vllm-openai"',
    )

    parser.add_argument(
        "-ig", "--ingest_dataset", type=bool, default=False, required=False, help='Set True to ingest dataset"'
    )

    parser.add_argument("-dbu", "--db_url", type=str, required=True, help="Vector DB URL")

    parser.add_argument("-dbs", "--db_schema", type=str, required=True, help="Vector DB Schema")

    parser.add_argument("-dbi", "--db_index", type=str, required=True, help="Vector DB Index Name")

    args = parser.parse_args()

    if args.ingest_dataset:
        langchain_doc = GetLangchainDataset(args)
        ingest_dataset(args, langchain_doc)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = args.langchain_token
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = args.huggingface_token

    chain = buildchain(args)
    run_test(args, chain)
