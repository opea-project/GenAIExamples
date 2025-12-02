# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Core DeepSearch implementation."""

from __future__ import annotations

import asyncio
import os
from typing import Any, List, Tuple

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import AgentType, CallbackType, CompType
from edgecraftrag.components.agent import Agent, stream_writer
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .config import load_config
from .logging_utils import format_terminal_str, log_status
from .postprocessing import postproc_answer as default_postproc_answer
from .postprocessing import postproc_plan as default_postproc_plan
from .postprocessing import postproc_query as default_postproc_query
from .utils import Role, import_module_from_path

DEFAULT_CONFIG = "./edgecraftrag/components/agents/deep_search/cfgs/default.json"


class Retrieval(BaseModel):
    step: str
    query: str
    retrieved: List[Any] = Field(...)
    reranked: List[Any] = Field(...)


class DeepSearchState(BaseModel):
    question: str
    query: str
    step: int
    num_retrievals: int
    answer: str

    plan: List[str] = Field(default_factory=list)
    retrievals: List[Retrieval] = Field(default_factory=list)
    context_chunk_ids: List[str] = Field(default_factory=list)
    search_summaries: List[str] = Field(default_factory=list)

    request: ChatCompletionRequest


class DeepSearchAgent(Agent):
    """Driver class orchestrating the deep search workflow."""

    def __init__(self, idx, name, pipeline_idx, cfg):
        super().__init__(name=name, agent_type=AgentType.DEEPSEARCH, pipeline_idx=pipeline_idx, configs=cfg)

        # Load the configuration
        # TODO: remove deep path
        self.cfg = load_config(DEFAULT_CONFIG)
        if idx is not None:
            self.idx = idx
        if "retrieve_top_k" in cfg:
            self.cfg.retrieve_top_k = cfg["retrieve_top_k"]
        if "rerank_top_k" in cfg:
            self.cfg.rerank_top_k = cfg["rerank_top_k"]
        if "mece_retrieval" in cfg:
            self.cfg.mece_retrieval = cfg["mece_retrieval"]
        if "max_retrievals" in cfg:
            self.cfg.max_retrievals = cfg["max_retrievals"]
        if "max_plan_steps" in cfg:
            self.cfg.max_plan_steps = cfg["max_plan_steps"]

        self.graph = self._build_graph()
        self._messages: List[dict] = []
        self.conversation_history: List[dict] = []

        postproc_module = None
        if self.cfg.postproc:
            try:
                postproc_module = import_module_from_path(self.cfg.postproc)
            except ImportError as exc:
                log_status(
                    "⚠️",
                    format_terminal_str(
                        f"Failed to import postproc module '{self.cfg.postproc}': {exc}", color="yellow"
                    ),
                )
        postproc_module = postproc_module or None
        self.postproc_query = getattr(postproc_module, "postproc_query", default_postproc_query)
        self.postproc_answer = getattr(postproc_module, "postproc_answer", default_postproc_answer)
        self.postproc_plan = getattr(postproc_module, "postproc_plan", default_postproc_plan)

    @classmethod
    def get_default_configs(cls):
        cfg = load_config(DEFAULT_CONFIG)
        return {
            "retrieve_top_k": cfg.retrieve_top_k,
            "rerank_top_k": cfg.rerank_top_k,
            "mece_retrieval": cfg.mece_retrieval,
            "max_retrievals": cfg.max_retrievals,
            "max_plan_steps": cfg.max_plan_steps,
        }

    def update(self, cfg):
        retrieve = cfg.get("retrieve_top_k", None)
        if retrieve and isinstance(retrieve, int):
            self.cfg.retrieve_top_k = retrieve
            self.configs["retrieve_top_k"] = retrieve

        rerank = cfg.get("rerank_top_k", None)
        if rerank and isinstance(rerank, int):
            self.cfg.rerank_top_k = rerank
            self.configs["rerank_top_k"] = rerank

        mr = cfg.get("mece_retrieval", None)
        if mr and isinstance(mr, int):
            self.cfg.mece_retrieval = mr
            self.configs["mece_retrieval"] = mr

        maxr = cfg.get("max_retrievals", None)
        if maxr and isinstance(maxr, int):
            self.cfg.max_retrievals = maxr
            self.configs["max_retrievals"] = maxr

        mps = cfg.get("max_plan_steps", None)
        if mps and isinstance(mps, int):
            self.cfg.max_plan_steps = mps
            self.configs["max_plan_steps"] = mps

    async def _build_init_messages(self, request: ChatCompletionRequest) -> List[dict]:
        if os.path.isfile(self.cfg.domain_knowledge):
            with open(self.cfg.domain_knowledge, "r", encoding="utf-8") as file:
                self.cfg.domain_knowledge = file.read()

        experiences_block = ""
        experience_status = True if request.tool_choice == "auto" else False
        if experience_status:
            log_status(
                "🔍",
                format_terminal_str(
                    "Retrieving experiences from experience knowledge base ...\n",
                    color="cyan",
                    bold=True,
                ),
            )
            _, query_search_result = await self.run_pipeline_query_search(request)
            raw_examples = query_search_result
            if isinstance(query_search_result, dict):
                raw_examples = query_search_result.get("results") or ""
            if isinstance(raw_examples, str):
                examples = [chunk for chunk in raw_examples.split("\n\n") if chunk.strip()]
            elif isinstance(raw_examples, list):
                examples = [chunk for chunk in raw_examples if isinstance(chunk, str) and chunk.strip()]
            else:
                examples = []
            if examples:
                num_retrieved = len(examples)
                num_max_examples = 3
                if num_retrieved > num_max_examples:
                    examples = examples[:num_max_examples]
                    log_status(
                        "📚",
                        f"Retrieved {format_terminal_str(str(num_retrieved), color='cyan', bold=True)} similar questions from experience database.",
                    )
                    log_status(
                        "⚠️",
                        f"Truncated to top {format_terminal_str(str(num_max_examples), color='cyan', bold=True)} examples for prompt.\n",
                    )
                else:
                    log_status(
                        "📚",
                        f"Retrieved {format_terminal_str(str(num_retrieved), color='cyan', bold=True)} similar questions from experience database.\n",
                    )
                experiences_block = self.cfg.prompt_templates.experiences.format(experiences="\n\n".join(examples))
        return [
            {
                "role": Role.SYSTEM.value,
                "content": self.cfg.prompt_templates.system.format(
                    system_instruction=self.cfg.system_instruction,
                    query_instruction=self.cfg.query_instruction,
                    domain_knowledge=self.cfg.domain_knowledge,
                    experiences=experiences_block,
                ),
            }
        ]

    async def _retrieve_and_rerank(
        self, state: DeepSearchState, mece_retrieve: bool = False
    ) -> Tuple[List[Any], List[Any], List[str]]:
        retrieval_query, rerank_query = self.postproc_query(state.query, state)
        mece_retrieve = mece_retrieve or self.cfg.mece_retrieval
        request = state.request
        request.messages = retrieval_query
        contexts = await self.run_pipeline_retrieve(request)
        # Llamaindex NodeWithScore Structure
        retrieved = contexts[CompType.RETRIEVER]

        if mece_retrieve:
            new_retrieved = [node for node in retrieved if node.node_id not in state.context_chunk_ids]
            # TODO: Using top_k from request, need to change?
            new_retrieved = new_retrieved[: request.k]
        else:
            new_retrieved = retrieved

        contexts[CompType.RETRIEVER] = new_retrieved

        request = state.request
        request.messages = rerank_query
        contexts = await self.run_pipeline_rerank(request, contexts)
        reranked = contexts[CompType.POSTPROCESSOR]
        reranked_chunk_ids = [node.node_id for node in reranked]
        return new_retrieved, reranked, state.context_chunk_ids + reranked_chunk_ids

    async def retrieve(self, state: DeepSearchState) -> dict:
        retrieved, reranked, updated_chunk_ids = await self._retrieve_and_rerank(state)
        log_status(
            "🔍",
            f"Retrieved {format_terminal_str(str(len(retrieved)), color='magenta', bold=True)} documents, "
            f"Reranked to top {format_terminal_str(str(len(reranked)), color='magenta', bold=True)}.",
        )
        await stream_writer(f"\n\n🔍 **Retrieved {str(len(retrieved))}, Reranked to top {str(len(reranked))}**\n\n")
        new_retrieval = Retrieval(
            step=state.plan[state.step],
            query=state.query,
            retrieved=retrieved,
            reranked=reranked,
        )
        return {
            "num_retrievals": state.num_retrievals + 1,
            "retrievals": [*state.retrievals, new_retrieval],
            "context_chunk_ids": updated_chunk_ids,
        }

    async def check_retrieved(self, state: DeepSearchState) -> str:
        log_status("🤔", format_terminal_str("Evaluating if more information is needed", color="green"))
        await stream_writer("\n\n🤔 **Evaluating if more information is needed**\n\n")
        contexts = self.cfg.prompt_templates.contexts.format(
            contexts="\n".join(
                [self.cfg.prompt_templates.context.format(context=doc.text) for doc in state.retrievals[-1].reranked]
            )
        )
        messages = [
            {
                "role": Role.SYSTEM.value,
                "content": contexts,
            },
            {
                "role": Role.SYSTEM.value,
                "content": self.cfg.prompt_templates.continue_decision,
            },
        ]
        self._messages.extend(messages)
        self.conversation_history.extend(messages)
        if state.num_retrievals >= self.cfg.max_retrievals:
            log_status(
                "⚠️",
                format_terminal_str(
                    f"Reached maximum retrievals: {self.cfg.max_retrievals}, stopping search\n",
                    color="yellow",
                    bold=True,
                ),
            )
            await stream_writer(f"\n\n⚠️ **Reached maximum retrievals: {self.cfg.max_retrievals}, stopping search**\n\n")
            return "stop"

        response = await self.llm_generate_astream_writer(state.request)

        message = {
            "role": Role.ASSISTANT.value,
            "content": response,
        }
        self._messages.append(message)
        self.conversation_history.append(message)
        if response.upper().startswith("NO"):
            log_status(
                "✅",
                format_terminal_str("Information is sufficient, moving to next step\n", color="green"),
            )
            await stream_writer("\n\n✅ **Information is sufficient, moving to next step**\n\n")
            return "stop"
        log_status(
            "🔄",
            format_terminal_str("Need more information, generating new query ...", color="green"),
        )
        await stream_writer("\n\n🔄 **Need more information, generating new query**\n\n")
        return "continue"

    async def generate_query(self, state: DeepSearchState) -> dict:
        await stream_writer("\n\n💡 **Generating a query to help to understand the question**\n\n")
        message = {
            "role": Role.SYSTEM.value,
            "content": self.cfg.prompt_templates.generate_query,
        }
        self._messages.append(message)
        self.conversation_history.append(message)

        response = await self.llm_generate_astream_writer(state.request)

        message = {
            "role": Role.ASSISTANT.value,
            "content": response,
        }
        self._messages.append(message)
        self.conversation_history.append(message)
        return {"query": response}

    async def execute_next_step(self, state: DeepSearchState) -> None:
        step = state.plan[state.step]
        title_str = format_terminal_str(
            f"Executing Step {state.step + 1}/{len(state.plan)}:",
            color="green",
            bold=True,
        )
        log_status("🚀", f"{title_str} {format_terminal_str(step, italic=True)}")
        log_status("💡", format_terminal_str("Generating the initial query ...", color="green"))
        await stream_writer(f'<agent title="Executing Step {state.step + 1}/{len(state.plan)}: {step}">')
        message = {
            "role": Role.SYSTEM.value,
            "content": f"Start to execute the step: {step}\n",
        }
        self._messages.append(message)
        self.conversation_history.append(message)

    async def finish_search(self, state: DeepSearchState) -> dict:
        await stream_writer("</agent>")
        return {"step": state.step + 1, "num_retrievals": 0}

    async def check_execution(self, state: DeepSearchState) -> str:
        if state.step >= len(state.plan):
            log_status("🏁", format_terminal_str("All planned steps completed", color="cyan", bold=True))
            await stream_writer('<agent title="All planned steps completed" tag="nofold"></agent>')
            return "stop"
        return "continue"

    async def make_plan(self, state: DeepSearchState) -> dict:
        log_status("📋", format_terminal_str("Making a plan ...", color="cyan", bold=True))
        await stream_writer('<agent title="Making a plan">')
        messages = [
            {
                "role": Role.USER.value,
                "content": state.question,
            },
            {
                "role": Role.SYSTEM.value,
                "content": self.cfg.prompt_templates.make_plan.format(plan_instruction=self.cfg.plan_instruction),
            },
        ]
        self._messages.extend(messages)
        self.conversation_history.extend(messages)

        response = await self.llm_generate(state.request, False)

        plan = self.postproc_plan(response, state, self.cfg)
        num_plan_step = len(plan)
        for i, step in enumerate(plan):
            step_num_str = format_terminal_str(f"Step{i+1: >2d}:", color="green", bold=True)
            step_str = format_terminal_str(step, bold=False, italic=True)
            suffix = "\n" if i == num_plan_step - 1 else ""
            log_status("📌", f"{step_num_str} {step_str}{suffix}")
            await stream_writer(f"📌 Step{i+1: >2d}: {step}\n\n")
        await stream_writer("</agent>")
        plan_prompt = self.cfg.prompt_templates.plan.format(
            plan_steps="\n".join(
                [self.cfg.prompt_templates.plan_step.format(num=i + 1, step=step) for i, step in enumerate(plan)]
            )
        )
        message = {
            "role": Role.ASSISTANT.value,
            "content": plan_prompt,
        }
        self._messages.append(message)
        self.conversation_history.append(message)
        return {"plan": plan, "step": 0, "num_retrievals": 0}

    async def summarize_search(self, state: DeepSearchState) -> dict:
        log_status("📝", format_terminal_str("Summarizing the search process ...", color="cyan", bold=True))
        await stream_writer("📝 **Summarizing the search process**")
        messages = [
            {
                "role": Role.SYSTEM.value,
                "content": self.cfg.recur_summarize_instruction,
            }
        ]
        self._messages.extend(messages)
        self.conversation_history.extend(messages)

        response = await self.llm_generate_astream_writer(state.request)

        message = {
            "role": Role.ASSISTANT.value,
            "content": response,
        }
        self.conversation_history.append(message)
        self._messages = [
            self._messages[0],
            self._messages[1],
            self._messages[3],
        ]
        self._messages.append(
            {
                "role": Role.ASSISTANT.value,
                "content": "The following is the summarized information from previous search steps:\n" + response,
            }
        )
        log_status("✅", format_terminal_str("Search process summarized\n", color="cyan", bold=True))
        await stream_writer("✅ **Search process summarized**")
        return {"search_summaries": [*state.search_summaries, response]}

    async def generate_answer(self, state: DeepSearchState) -> dict:
        log_status("📝", format_terminal_str("Generating the final answer ...", color="cyan", bold=True))
        await stream_writer('<agent title="Generating the final answer ..." tag="nofold"></agent>')

        if self.cfg.use_summarized_context and state.search_summaries:
            plan_with_information = "Plan with Summarized Information:\n"
            for i, step in enumerate(state.plan):
                plan_with_information += f"Step {i+1}: {step}\n"
                if i < len(state.search_summaries):
                    plan_with_information += f"- Summary: {state.search_summaries[i]}\n\n"
                else:
                    plan_with_information += "- Summary: N/A\n\n"
        else:
            if not self.cfg.mece_retrieval:
                plan_with_information = (
                    "Plan:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(state.plan)]) + "\n\n"
                )
                plan_with_information += "Retrieved Information:\n"
                presented_ids = []
                for retrieval in state.retrievals:
                    for doc in retrieval.reranked:
                        node_id = doc.node_id
                        if node_id not in presented_ids:
                            plan_with_information += f"{doc.text}\n\n"
                            presented_ids.append(node_id)
            else:
                plan_with_information = "Plan with Retrieved Information:\n"
                for i, step in enumerate(state.plan):
                    plan_with_information += f"Step {i+1}: {step}\n"
                    related_docs = []
                    for retrieval in state.retrievals:
                        if retrieval.step == step:
                            related_docs = retrieval.reranked
                            break
                    for doc in related_docs:
                        plan_with_information += f"- {doc.text}\n"
                    plan_with_information += "\n"

        self._messages = [
            {
                "role": Role.SYSTEM.value,
                "content": self.cfg.answer_instruction.format(
                    question=state.question,
                    plan_with_information=plan_with_information,
                ),
            }
        ]
        self.conversation_history.extend(self._messages)

        response = await self.llm_generate_astream_writer(state.request)

        self.conversation_history.append(
            {
                "role": Role.ASSISTANT.value,
                "content": response,
            }
        )
        answer = self.postproc_answer(response, state)
        title_str = format_terminal_str("Final Answer:", color="blue", bold=True)
        log_status(
            "✅",
            format_terminal_str(
                f"{title_str}\n{format_terminal_str(answer, italic=True, bold=True)}",
                color="blue",
                bold=True,
            ),
        )
        return {"answer": answer}

    def _build_graph(self):
        search = StateGraph(DeepSearchState)
        search.add_node("generate_query", self.generate_query)
        search.add_node("retrieve", self.retrieve)
        search.add_node("finish_search", self.finish_search)

        search.add_edge(START, "generate_query")
        search.add_edge("generate_query", "retrieve")
        search.add_conditional_edges(
            "retrieve",
            self.check_retrieved,
            {
                "stop": "finish_search",
                "continue": "generate_query",
            },
        )
        if self.cfg.recur_summarize_instruction:
            search.add_edge("finish_search", "summarize")
            search.add_node("summarize", self.summarize_search)
            search.add_edge("summarize", END)
        else:
            search.add_edge("finish_search", END)

        deep_search = StateGraph(DeepSearchState)
        deep_search.add_node("make_plan", self.make_plan)
        deep_search.add_node("execute_search_step", self.execute_next_step)
        deep_search.add_node("search", search.compile())
        deep_search.add_node("final_answer", self.generate_answer)

        deep_search.add_edge(START, "make_plan")
        deep_search.add_edge("make_plan", "execute_search_step")
        deep_search.add_edge("execute_search_step", "search")
        deep_search.add_conditional_edges(
            "search",
            self.check_execution,
            {
                "stop": "final_answer",
                "continue": "execute_search_step",
            },
        )
        deep_search.add_edge("final_answer", END)

        return deep_search.compile()

    def generate_report(self, result: dict, report_path: str) -> str:
        import datetime

        log_status(
            "📝",
            format_terminal_str(
                f"Generating markdown report at {report_path}",
                color="cyan",
                bold=True,
            ),
        )
        question = result.get("question", "No question provided")
        plan = result.get("plan", [])
        answer = result.get("answer", "No answer provided")
        retrievals = result.get("retrievals", [])
        search_summaries = result.get("search_summaries", [])
        graph_mermaid = result.get("graph_mermaid", "")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = [
            "# Deep Search Report",
            f"*Generated on: {timestamp}*",
            "",
            "## Original Question",
            f"> {question}",
            "",
            "## Research Plan",
        ]
        for i, step in enumerate(plan):
            report.append(f"{i+1}. {step}")
        report.append("")
        report.append("---")
        report.append("## Search Statistics")
        report.append(f"- **Total Retrieval Operations:** {len(retrievals)}")
        if retrievals:
            total_docs = sum(len(r.retrieved) for r in retrievals)
            report.append(f"- **Total Documents Retrieved:** {total_docs}")
            total_reranked = sum(len(r.reranked) for r in retrievals)
            report.append(f"- **Total Documents After Reranking:** {total_reranked}")
        report.append("")
        report.append("---")
        report.append("## Final Answer")
        report.append(answer)
        if search_summaries:
            report.append("## Search Summaries")
            for i, summary in enumerate(search_summaries):
                report.append(f"### Summary for Step {i+1}")
                report.append(summary)
            report.append("")
            report.append("---")
        report.append("## Search Process Details")
        for i, retrieval in enumerate(retrievals):
            step_index = i + 1
            step_desc = retrieval.step
            report.append(f"### Retrieval {step_index}: {step_desc}")
            report.append(f'**Query:** "{retrieval.query}"')
            report.append("#### Retrieved Documents Summary")
            for j, doc in enumerate(retrieval.reranked[:3]):
                doc_content = doc.text
                if len(doc_content) > 500:
                    doc_content = doc_content[:500] + "..."
                doc_content = doc_content.replace("\n", "\n> ")
                report.append(f"**Document {j+1}:**")
                report.append(f"> {doc_content}")
                report.append("")
            if i < len(retrievals) - 1:
                report.append("---")
        if graph_mermaid:
            report.append("## Search Graph")
            report.append("```mermaid")
            report.append(graph_mermaid)
            report.append("```")
            report.append("")
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write("\n\n".join(report))
        return report_path

    # Implement abstract run function
    # callback dispatcher
    async def run(self, **kwargs) -> Any:
        if "cbtype" in kwargs:
            if kwargs["cbtype"] == CallbackType.RUNAGENT:
                request = kwargs["chat_request"]

                log_status(
                    "🤿",
                    f"{format_terminal_str('Starting DeepSearch:', color='cyan', bold=True)} {format_terminal_str(request.messages, italic=True)}\n",
                )
                state = DeepSearchState(
                    question=request.messages,
                    query="",
                    step=0,
                    num_retrievals=0,
                    answer="",
                    plan=[],
                    retrievals=[],
                    request=request,
                )
                self._messages = await self._build_init_messages(request)

                async def async_gen():
                    async for event, chunk in self.graph.astream(state, subgraphs=True, stream_mode="custom"):
                        yield chunk
                        await asyncio.sleep(0)

                # log_status("✅", format_terminal_str("DeepSearch process completed", color="cyan", bold=True))
                # result["conversation"] = [*self.conversation_history]
                # result["graph_mermaid"] = self.graph.get_graph(xray=True).draw_mermaid()
                return async_gen()
