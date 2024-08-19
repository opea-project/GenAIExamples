# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Any, Literal, Sequence, TypedDict

from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from ..base_agent import BaseAgent
from .prompt import DOC_GRADER_PROMPT, RAG_PROMPT

instruction = "Retrieved document is not sufficient or relevant to answer the query. Reformulate the query to search knowledge base again."
MAX_RETRY = 3


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]
    output: str
    doc_score: str
    query_time: str


class QueryWriter:
    """Invokes llm to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the response appended to messages
    """

    def __init__(self, llm_endpoint, model_id, tools):
        if isinstance(llm_endpoint, HuggingFaceEndpoint):
            self.llm = ChatHuggingFace(llm=llm_endpoint, model_id=model_id).bind_tools(tools)
        elif isinstance(llm_endpoint, ChatOpenAI):
            self.llm = llm_endpoint.bind_tools(tools)

    def __call__(self, state):
        print("---CALL QueryWriter---")
        messages = state["messages"]

        response = self.llm.invoke(messages)
        # We return a list, because this will get added to the existing list
        return {"messages": [response], "output": response}


class Retriever:
    @classmethod
    def create(cls, tools_descriptions):
        return ToolNode(tools_descriptions)


class DocumentGrader:
    """Determines whether the retrieved documents are relevant to the question.

    Args:
        state (messages): The current state

    Returns:
        str: A decision for whether the documents are relevant or not
    """

    def __init__(self, llm_endpoint, model_id=None):
        class grade(BaseModel):
            """Binary score for relevance check."""

            binary_score: str = Field(description="Relevance score 'yes' or 'no'")

        # Prompt
        prompt = PromptTemplate(
            template=DOC_GRADER_PROMPT,
            input_variables=["context", "question"],
        )

        if isinstance(llm_endpoint, HuggingFaceEndpoint):
            llm = ChatHuggingFace(llm=llm_endpoint, model_id=model_id).bind_tools([grade])
        elif isinstance(llm_endpoint, ChatOpenAI):
            llm = llm_endpoint.bind_tools([grade])
        output_parser = PydanticToolsParser(tools=[grade], first_tool_only=True)
        self.chain = prompt | llm | output_parser

    def __call__(self, state) -> Literal["generate", "rewrite"]:
        print("---CALL DocumentGrader---")
        messages = state["messages"]
        last_message = messages[-1]  # the latest retrieved doc

        question = messages[0].content  # the original query
        docs = last_message.content

        scored_result = self.chain.invoke({"question": question, "context": docs})

        score = scored_result.binary_score

        if score.startswith("yes"):
            print("---DECISION: DOCS RELEVANT---")
            return {"doc_score": "generate"}

        else:
            print(f"---DECISION: DOCS NOT RELEVANT, score is {score}---")

            return {"messages": [HumanMessage(content=instruction)], "doc_score": "rewrite"}


class TextGenerator:
    """Generate answer.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with re-phrased question
    """

    def __init__(self, llm_endpoint, model_id=None):
        # Chain
        # prompt = rlm_rag_prompt
        prompt = RAG_PROMPT
        self.rag_chain = prompt | llm_endpoint | StrOutputParser()

    def __call__(self, state):
        print("---GENERATE---")
        messages = state["messages"]
        question = messages[0].content
        query_time = state["query_time"]

        # find the latest retrieved doc
        # which is a ToolMessage
        for m in state["messages"][::-1]:
            if isinstance(m, ToolMessage):
                last_message = m
                break

        question = messages[0].content
        docs = last_message.content

        # Run
        response = self.rag_chain.invoke({"context": docs, "question": question, "time": query_time})
        print("@@@@ Used this doc for generation:\n", docs)
        print("@@@@ Generated response: ", response)
        return {"messages": [response], "output": response}


class RAGAgent(BaseAgent):
    def __init__(self, args):
        super().__init__(args)

        # Define Nodes
        document_grader = DocumentGrader(self.llm_endpoint, args.model)
        query_writer = QueryWriter(self.llm_endpoint, args.model, self.tools_descriptions)
        text_generator = TextGenerator(self.llm_endpoint)
        retriever = Retriever.create(self.tools_descriptions)

        # Define graph
        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("query_writer", query_writer)
        workflow.add_node("retrieve", retriever)
        workflow.add_node("doc_grader", document_grader)
        workflow.add_node("generate", text_generator)

        # connect as graph
        workflow.add_edge(START, "query_writer")
        workflow.add_conditional_edges(
            "query_writer",
            tools_condition,
            {
                "tools": "retrieve",  # if tools_condition return 'tools', then go to 'retrieve'
                END: END,  # if tools_condition return 'END', then go to END
            },
        )

        workflow.add_edge("retrieve", "doc_grader")

        workflow.add_conditional_edges(
            "doc_grader",
            self.should_retry,
            {
                False: "generate",
                True: "query_writer",
            },
        )
        workflow.add_edge("generate", END)

        self.app = workflow.compile()

    def should_retry(self, state):
        # first check how many retry attempts have been made
        num_retry = 0
        for m in state["messages"]:
            if instruction in m.content:
                num_retry += 1

        print("**********Num retry: ", num_retry)

        if (num_retry < MAX_RETRY) and (state["doc_score"] == "rewrite"):
            return True
        else:
            return False

    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)]}

    async def stream_generator(self, query, config):
        initial_state = self.prepare_initial_state(query)
        try:
            async for event in self.app.astream(initial_state, config=config):
                for node_name, node_state in event.items():
                    yield f"--- CALL {node_name} ---\n"
                    for k, v in node_state.items():
                        if v is not None:
                            yield f"{k}: {v}\n"

                yield f"data: {repr(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield str(e)

    async def non_streaming_run(self, query, config):
        initial_state = self.prepare_initial_state(query)
        try:
            async for s in self.app.astream(initial_state, config=config, stream_mode="values"):
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()

            last_message = s["messages"][-1]
            print("******Response: ", last_message.content)
            return last_message.content
        except Exception as e:
            return str(e)
