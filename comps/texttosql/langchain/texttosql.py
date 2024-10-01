# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Type, Union

from langchain.agents import create_react_agent
from langchain.agents.agent import AgentExecutor, RunnableAgent
from langchain.agents.agent_types import AgentType
from langchain.agents.mrkl import prompt as react_prompt
from langchain.chains.llm import LLMChain
from langchain_community.agent_toolkits.sql.prompt import SQL_PREFIX, SQL_SUFFIX
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.tools.sql_database.prompt import QUERY_CHECKER
from langchain_community.tools.sql_database.tool import InfoSQLDatabaseTool, ListSQLDatabaseTool
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.callbacks import AsyncCallbackManagerForToolRun, BaseCallbackManager, CallbackManagerForToolRun
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, root_validator
from langchain_core.tools import BaseTool
from langchain_huggingface import HuggingFaceEndpoint
from sqlalchemy.engine import Result

from comps import CustomLogger

generation_params = {
    "max_new_tokens": 1024,
    "top_k": 10,
    "top_p": 0.95,
    "temperature": 0.01,
    "repetition_penalty": 1.03,
    "streaming": True,
}


TGI_LLM_ENDPOINT = os.environ.get("TGI_LLM_ENDPOINT")

llm = HuggingFaceEndpoint(
    endpoint_url=TGI_LLM_ENDPOINT,
    task="text-generation",
    **generation_params,
)

sql_params = {
    "max_string_length": 3600,
}

logger = CustomLogger("comps-texttosql")
logflag = os.getenv("LOGFLAG", False)

# https://github.com/langchain-ai/langchain/issues/23585


class BaseSQLDatabaseTool(BaseModel):
    """Base tool for interacting with a SQL database."""

    db: SQLDatabase = Field(exclude=True)

    class Config(BaseTool.Config):
        pass


class _QuerySQLDataBaseToolInput(BaseModel):
    query: str = Field(..., description="A detailed and correct SQL query.")


class CustomQuerySQLDataBaseTool(BaseSQLDatabaseTool, BaseTool):
    """Tool for querying a SQL database."""

    name: str = "sql_db_query"
    description: str = """
    Execute a SQL query against the database and get back the result..
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    args_schema: Type[BaseModel] = _QuerySQLDataBaseToolInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[str, Sequence[Dict[str, Any]], Result]:
        """Execute the query, return the results or an error message."""
        logger.info("query: {}".format(query))
        query = query.replace("\nObservation", "")
        result = self.db.run_no_throw(query)
        return result


class _InfoSQLDatabaseToolInput(BaseModel):
    table_names: str = Field(
        ...,
        description=(
            "A comma-separated list of the table names for which to return the schema. "
            "Example input: 'table1, table2, table3'"
        ),
    )


class CustomInfoSQLDatabaseTool(BaseSQLDatabaseTool, BaseTool):
    """Tool for getting metadata about a SQL database."""

    name: str = "sql_db_schema"
    description: str = "Get the schema and sample rows for the specified SQL tables."
    args_schema: Type[BaseModel] = _InfoSQLDatabaseToolInput

    def _run(
        self,
        table_names: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the schema for tables in a comma-separated list."""
        table_names = table_names.replace("\nObservation", "")  # this changed
        return self.db.get_table_info_no_throw([t.strip() for t in table_names.split(",")])


class _ListSQLDataBaseToolInput(BaseModel):
    tool_input: str = Field("", description="An empty string")


class CustomListSQLDatabaseTool(BaseSQLDatabaseTool, BaseTool):
    """Tool for getting tables names."""

    name: str = "sql_db_list_tables"
    description: str = "Input is an empty string, output is a comma-separated list of tables in the database."
    args_schema: Type[BaseModel] = _ListSQLDataBaseToolInput

    def _run(
        self,
        tool_input: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get a comma-separated list of table names."""
        return ", ".join(self.db.get_usable_table_names())


class _QuerySQLCheckerToolInput(BaseModel):
    query: str = Field(..., description="A detailed and SQL query to be checked.")


class CustomQuerySQLCheckerTool(BaseSQLDatabaseTool, BaseTool):
    """Use an LLM to check if a query is correct.

    Adapted from https://www.patterns.app/blog/2023/01/18/crunchbot-sql-analyst-gpt/
    """

    template: str = QUERY_CHECKER
    llm: BaseLanguageModel
    llm_chain: Any = Field(init=False)
    name: str = "sql_db_query_checker"
    description: str = """
    Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with sql_db_query!
    """
    args_schema: Type[BaseModel] = _QuerySQLCheckerToolInput

    @root_validator(pre=True)
    def initialize_llm_chain(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Initializes the LLM chain if it does not exist in the given values dictionary."""

        if "llm_chain" not in values:
            values["llm_chain"] = LLMChain(
                llm=values.get("llm"),  # type: ignore[arg-type]
                prompt=PromptTemplate(template=QUERY_CHECKER, input_variables=["dialect", "query"]),
            )

        if values["llm_chain"].prompt.input_variables != ["dialect", "query"]:
            raise ValueError("LLM chain for QueryCheckerTool must have input variables ['query', 'dialect']")

        return values

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the LLM to check the query."""
        return self.llm_chain.predict(
            query=query,
            dialect=self.db.dialect,
            callbacks=run_manager.get_child() if run_manager else None,
        )

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.llm_chain.apredict(
            query=query,
            dialect=self.db.dialect,
            callbacks=run_manager.get_child() if run_manager else None,
        )


class CustomSQLDatabaseToolkit(SQLDatabaseToolkit):
    """Provides functionality to manage and manipulate SQL databases in customized way."""

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        list_sql_database_tool = CustomListSQLDatabaseTool(db=self.db)
        info_sql_database_tool_description = (
            "Input to this tool is a comma-separated list of tables, output is the "
            "schema and sample rows for those tables. "
            "Be sure that the tables actually exist by calling "
            f"{list_sql_database_tool.name} first! "
            "Example Input: table1, table2, table3"
        )
        info_sql_database_tool = CustomInfoSQLDatabaseTool(db=self.db, description=info_sql_database_tool_description)
        query_sql_database_tool_description = (
            "Input to this tool is a detailed and correct SQL query, output is a "
            "result from the database. If the query is not correct, an error message "
            "will be returned. If an error is returned, rewrite the query, check the "
            "query, and try again. If you encounter an issue with Unknown column "
            f"'xxxx' in 'field list', use {info_sql_database_tool.name} "
            "to query the correct table fields."
        )
        query_sql_database_tool = CustomQuerySQLDataBaseTool(
            db=self.db, description=query_sql_database_tool_description
        )
        query_sql_checker_tool_description = (
            "Use this tool to double check if your query is correct before executing "
            "it. Always use this tool before executing a query with "
            f"{query_sql_database_tool.name}!"
        )
        query_sql_checker_tool = CustomQuerySQLCheckerTool(
            db=self.db, llm=self.llm, description=query_sql_checker_tool_description
        )
        return [
            query_sql_database_tool,
            info_sql_database_tool,
            list_sql_database_tool,
            query_sql_checker_tool,
        ]


def custom_create_sql_agent(
    llm: BaseLanguageModel,
    toolkit: Optional[SQLDatabaseToolkit] = None,
    callback_manager: Optional[BaseCallbackManager] = None,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    format_instructions: Optional[str] = None,
    top_k: int = 3,
    max_iterations: Optional[int] = 15,
    max_execution_time: Optional[float] = None,
    early_stopping_method: str = "force",
    verbose: bool = False,
    agent_executor_kwargs: Optional[Dict[str, Any]] = None,
    *,
    db: Optional[SQLDatabase] = None,
    prompt: Optional[BasePromptTemplate] = None,
    **kwargs: Any,
) -> AgentExecutor:
    """Creates a SQL agent with specified parameters."""

    tools = toolkit.get_tools()
    if prompt is None:
        prefix = prefix or SQL_PREFIX
        prefix = prefix.format(dialect=toolkit.dialect, top_k=top_k)
    else:
        if "top_k" in prompt.input_variables:
            prompt = prompt.partial(top_k=str(top_k))
        if "dialect" in prompt.input_variables:
            prompt = prompt.partial(dialect=toolkit.dialect)
        if any(key in prompt.input_variables for key in ["table_info", "table_names"]):
            db_context = toolkit.get_context()
            if "table_info" in prompt.input_variables:
                prompt = prompt.partial(table_info=db_context["table_info"])
                tools = [tool for tool in tools if not isinstance(tool, InfoSQLDatabaseTool)]
            if "table_names" in prompt.input_variables:
                prompt = prompt.partial(table_names=db_context["table_names"])
                tools = [tool for tool in tools if not isinstance(tool, ListSQLDatabaseTool)]

    if prompt is None:
        format_instructions = format_instructions or react_prompt.FORMAT_INSTRUCTIONS
        template = "\n\n".join(
            [
                prefix,
                "{tools}",
                format_instructions,
                suffix or SQL_SUFFIX,
            ]
        )
        prompt = PromptTemplate.from_template(template)

    agent = RunnableAgent(
        runnable=create_react_agent(llm, tools, prompt),
        input_keys_arg=["input"],
        return_keys_arg=["output"],
        **kwargs,
    )

    return AgentExecutor(
        name="SQL Agent Executor",
        agent=agent,
        tools=tools,
        callback_manager=callback_manager,
        verbose=verbose,
        max_iterations=max_iterations,
        max_execution_time=max_execution_time,
        early_stopping_method=early_stopping_method,
        handle_parsing_errors=True,
        **(agent_executor_kwargs or {}),
    )


def execute(input, url):
    """Execute a SQL query using the custom SQL agent.

    Args:
        input (str): The user's input.
        url (str): The URL of the database to connect to.

    Returns:
        dict: The result of the SQL execution.
    """
    db = SQLDatabase.from_uri(url, **sql_params)
    logger.info("Starting Agent")
    agent_executor = custom_create_sql_agent(
        llm=llm,
        verbose=True,
        toolkit=CustomSQLDatabaseToolkit(llm=llm, db=db),
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        agent_executor_kwargs={"return_intermediate_steps": True},
    )

    result = agent_executor.invoke(input)

    query = []
    for log, _ in result["intermediate_steps"]:
        if log.tool == "sql_db_query":
            query.append(log.tool_input)
    result["sql"] = query[0].replace("Observation", "")
    return result
