# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
from copy import deepcopy
from typing import Any, List

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import AgentType, CallbackType, CompType
from edgecraftrag.components.agent import Agent, Retrieval, stream_writer
from edgecraftrag.components.agents.utils import ROLE, build_document_node_block, format_terminal_str
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class PromptTemplates(BaseModel):
    system: str
    generate_query: str
    context: str
    contexts: str
    continue_decision: str


class Config(BaseModel):
    system_instruction: str
    query_instruction: str
    answer_instruction: str
    domain_knowledge: str = ""
    max_retrievals: int = 3
    prompt_templates: PromptTemplates


DEFAULT_CONFIG = {
    "system_instruction": "You will be provided with a question from a user, and you need to create queries and execute them based on the question for the final answer.\nYou should only use the information provided in the search results to answer the user's question. \nMake your response in the same language as the user's question./no_think",
    "query_instruction": 'Every time when asked if more information is needed, check the retrieved contexts and try to identify new content that is related. Then based on what you get and all above, decide if a new query is needed to gather more potential useful information. The query should be a very concise and clear sub-question that is specific to the user\'s question. A good query should include all the related actions or keywords that can help to retrieve the most related context. Response with the query directly.\nDO NOT use any prefix, such as "Query:"/no_think',
    "answer_instruction": "You have been provided with a question from user:\n{question}\n\nThe following are the plan steps you generated and the corresponding retrieved information:\n{plan_with_information}\n\nBased on the above, come up with a final answer for the user's question. Format the answer as a list of steps that can guide the user to solve the problem.\n\nCitation rules (MUST follow):\n1) Use only the provided DOCUMENT_NODE evidence.\n2) For each claim based on DOCUMENT_NODE_CONTEXT, append a citation after the current paragraph using:\n   - Chinese answer: (来自 [DOCUMENT_NODE_SOURCE](DOCUMENT_NODE_FILE_PATH))\n   - Non-Chinese answer: (from [DOCUMENT_NODE_SOURCE](DOCUMENT_NODE_FILE_PATH))\n3) At the end of your answer, output:\n\n --- \n\n### Document Source:\n- DOCUMENT_NODE_SOURCE\n\nOnly list unique DOCUMENT_NODE_SOURCE values (deduplicated). Do NOT output links/URLs/paths in this final Document Source block./no_think",
    "domain_knowledge": "",
    "max_retrievals": 3,
    "prompt_templates": {
        "system": """{system_instruction}\n\n{query_instruction}\n\n{domain_knowledge}\n\n.""",
        "generate_query": "Now generate a query for the next retrieval.",
        "context": """<context>\n{context}\n</context>\n""",
        "contexts": """The following are the retrieved contexts for current query.\n{contexts}\n.""",
        "continue_decision": "Is more information needed? Answer Yes or No. Then explain why or why not.",
    },
}


class QnaState(BaseModel):
    question: str
    query: str
    num_retrievals: int
    answer: str

    retrievals: List[Retrieval] = Field(default_factory=list)
    context_chunk_ids: List[str] = Field(default_factory=list)
    request: ChatCompletionRequest


class SimpleRAGAgent(Agent):

    def __init__(self, idx, name, pipeline_idx, cfg):
        super().__init__(name=name, agent_type=AgentType.SIMPLE, pipeline_idx=pipeline_idx, configs=cfg)
        cfg = cfg or {}
        merged_cfg = {**DEFAULT_CONFIG, **cfg}
        merged_cfg["prompt_templates"] = {
            **DEFAULT_CONFIG["prompt_templates"],
            **cfg.get("prompt_templates", {}),
        }
        self.cfg = Config(**merged_cfg)
        self.configs = merged_cfg

        self.graph = self._build_graph()
        self._messages = []
        self.conversation_history = []
        self.retrievals: List[Retrieval] = []
        if idx is not None:
            self.idx = idx
        self.max_retrievals = int(self.cfg.max_retrievals)
        self.postproc_query = postproc_query
        self.postproc_answer = postproc_answer

    @classmethod
    def get_default_configs(cls):
        return deepcopy(DEFAULT_CONFIG)

    def update(self, cfg):
        max_r = cfg.get("max_retrievals", None)
        if max_r and isinstance(max_r, int):
            self.max_retrievals = int(max_r)
            self.configs["max_retrievals"] = self.max_retrievals
            self.cfg.max_retrievals = self.max_retrievals

        for key in ["system_instruction", "query_instruction", "answer_instruction", "domain_knowledge"]:
            value = cfg.get(key, None)
            if value and isinstance(value, str):
                setattr(self.cfg, key, value)
                self.configs[key] = value

        prompt_templates = cfg.get("prompt_templates", None)
        if prompt_templates and isinstance(prompt_templates, dict):
            updated_templates = {
                **self.cfg.prompt_templates.model_dump(),
                **prompt_templates,
            }
            self.cfg.prompt_templates = PromptTemplates(**updated_templates)
            self.configs["prompt_templates"] = updated_templates

        return True

    def _build_graph(self):

        qnagraph = StateGraph(QnaState)
        qnagraph.add_node("generate_query", self.generate_query)
        qnagraph.add_node("retrieve", self.retrieve)
        qnagraph.add_node("final_answer", self.generate_answer)

        qnagraph.add_edge(START, "generate_query")
        qnagraph.add_edge("generate_query", "retrieve")
        qnagraph.add_conditional_edges(
            "retrieve", self.check_retrieved, {"stop": "final_answer", "continue": "generate_query"}
        )
        qnagraph.add_edge("final_answer", END)

        return qnagraph.compile()

    async def retrieve(self, state: QnaState) -> dict:
        # print(f"State Retrieve {state}")
        request = state.request
        request.messages = state.query
        contexts = await self.run_pipeline_retrieve_and_rerank(request)

        retrieved = contexts[CompType.RETRIEVER]
        reranked = contexts[CompType.POSTPROCESSOR]
        print(
            "🔍",
            f"Retrieved {format_terminal_str(str(len(retrieved)), color='magenta', bold=True)} documents, Reranked to top {format_terminal_str(str(len(reranked)), color='magenta', bold=True)}.",
        )
        await stream_writer(
            f"\n\n🔍 **Retrieved {str(len(retrieved))} documents, Reranked to top {str(len(reranked))}**\n\n"
        )

        new_retrieval = Retrieval(step=state.num_retrievals, query=state.query, retrieved=retrieved, reranked=reranked)
        return {
            "num_retrievals": state.num_retrievals + 1,
            "retrievals": [*state.retrievals, new_retrieval],
        }

    async def generate_query(self, state: QnaState) -> dict:
        # print(f"State generate_query {state}")
        await stream_writer('<agent title="Understanding the user\'s question">')

        messages = [
            {"role": ROLE.USER, "content": state.question},
            {"role": ROLE.SYSTEM, "content": self.cfg.prompt_templates.generate_query},
        ]
        self._messages.extend(messages)
        self.conversation_history.extend(messages)

        response = await self.llm_generate_astream_writer(state.request)

        message = {"role": ROLE.ASSISTANT, "content": response}
        self._messages.append(message)
        self.conversation_history.append(message)
        return {
            "query": response,
        }

    async def check_retrieved(self, state: QnaState) -> str:
        # print(f"State check_retrieved {state}")
        print("🤔", format_terminal_str("Evaluating if more information is needed", color="green"))
        await stream_writer("🤔 **Evaluating if more information is needed...**\n\n")

        # Format context for the next decision
        contexts = self.cfg.prompt_templates.contexts.format(
            contexts="\n".join(
                [self.cfg.prompt_templates.context.format(context=doc.text) for doc in state.retrievals[-1].reranked]
            )
        )
        messages = [
            {"role": ROLE.SYSTEM, "content": contexts},
            {"role": ROLE.SYSTEM, "content": self.cfg.prompt_templates.continue_decision},
        ]
        self._messages.extend(messages)
        self.conversation_history.extend(messages)
        if state.num_retrievals >= self.max_retrievals:
            print(
                "⚠️",
                format_terminal_str(
                    f"Reached maximum retrievals: {self.max_retrievals}, stopping search\n", color="yellow", bold=True
                ),
            )
            await stream_writer(
                f"\n\n⚠️ **Reached maximum retrievals: {self.max_retrievals}, stopping searching...**\n\n</agent>"
            )
            return "stop"
        else:
            response = await self.llm_generate_astream_writer(state.request)
            message = {"role": ROLE.ASSISTANT, "content": response}
            self._messages.append(message)
            self.conversation_history.append(message)
            if response.upper().startswith("NO"):
                print("✅", format_terminal_str("Information is sufficient, moving to next step\n", color="green"))
                await stream_writer("\n\n✅ **Information is sufficient, moving to next step...**\n\n</agent>")
                return "stop"
            else:
                print("🔄", format_terminal_str("Need more information, generating new query ...", color="green"))
                await stream_writer("\n\n🔄 **Need more information, generating new query...**\n\n</agent>")
                return "continue"

    async def generate_answer(self, state: QnaState) -> dict:
        # print(f"State generate_answer {state}")
        print("📝", format_terminal_str("Generating the final answer ...", color="cyan", bold=True))
        await stream_writer('<agent title="Generating the final answer ..." tag="nofold"></agent>')
        plan_with_information = ""
        prev_step = ""
        for i, r in enumerate(state.retrievals):
            if r.step != prev_step:
                plan_with_information += f"Step {i+1}\n\nRetrieved:\n"
            for doc in r.reranked:
                plan_with_information += build_document_node_block(doc)
            plan_with_information += "\n"
            prev_step = r.step

        self._messages = [
            {
                "role": ROLE.SYSTEM,
                "content": self.cfg.answer_instruction.format(
                    question=state.question, plan_with_information=plan_with_information
                ),
            }
        ]
        self.conversation_history.extend(self._messages)

        response = await self.llm_generate_astream_writer(state.request)

        self.conversation_history.append({"role": ROLE.ASSISTANT, "content": response})
        answer = self.postproc_answer(response, state)
        title_str = format_terminal_str("Final Answer:", color="blue", bold=True)
        print(
            "✅",
            format_terminal_str(
                f"{title_str}\n{format_terminal_str(answer, italic=True, bold=True)}", color="blue", bold=True
            ),
        )
        return {"answer": answer}

    # Implement abstract run function
    # callback dispatcher
    async def run(self, **kwargs) -> Any:
        if "cbtype" in kwargs:
            if kwargs["cbtype"] == CallbackType.RUNAGENT:
                request = kwargs["chat_request"]
                self.retrievals.clear()

                print(
                    "🤿",
                    f"{format_terminal_str('Starting DeepSearch:', color='cyan', bold=True)} {format_terminal_str(request.messages, bold=False, italic=True)}\n",
                )
                # Initialize state
                state = QnaState(
                    question=request.messages, query="", num_retrievals=0, answer="", retrievals=[], request=request
                )
                self._messages = self._build_init_messages(request.messages)

                async def async_gen():
                    final_state = None
                    async for mode, chunk in self.graph.astream(state, stream_mode=["custom", "values"]):
                        if mode == "custom":
                            yield chunk
                        elif mode == "values":
                            final_state = chunk
                        await asyncio.sleep(0)
                    if isinstance(final_state, dict):
                        self.retrievals.clear()
                        self.retrievals.extend(final_state.get("retrievals", []))

                print("✅", format_terminal_str("RAG process completed", color="cyan", bold=True))
                return async_gen()

    def _build_init_messages(self, question) -> List[dict]:
        return [
            {
                "role": ROLE.SYSTEM,
                "content": self.cfg.prompt_templates.system.format(
                    system_instruction=self.cfg.system_instruction,
                    query_instruction=self.cfg.query_instruction,
                    domain_knowledge=self.cfg.domain_knowledge,
                ),
            }
        ]


def postproc_query(text, state):
    """Default post-process the response text generated for new query.

    This function is a placeholder for any specific post-processing logic needed.
    The returned values are a tuple of (retrieval_query, rerank_query).
    """
    print("💡", f"{format_terminal_str('Query generated:', color='cyan', bold=True)} '{text}'")
    # Default use the raw response text as the query for both retrieval and rerank
    return text, text


def postproc_answer(text, state):
    return text
