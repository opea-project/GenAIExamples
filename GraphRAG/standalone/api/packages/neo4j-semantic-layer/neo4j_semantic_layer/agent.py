from typing import Any, List, Tuple

from pydantic import BaseModel, Field

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema import AIMessage, HumanMessage
from langchain.tools.render import format_tool_to_openai_function
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI

from neo4j_semantic_layer.company_tool import company_tool
from neo4j_semantic_layer.cypher_tool import cypher_tool

llm = ChatOpenAI(temperature=0, model="gpt-4", streaming=True)

tools = [company_tool, cypher_tool]

llm_with_tools = llm.bind_tools(tools)

from langchain.agents import initialize_agent, AgentType

agent_executor = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION)
