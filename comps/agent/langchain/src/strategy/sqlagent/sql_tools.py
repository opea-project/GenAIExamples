# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.utilities import SQLDatabase


def connect_to_db(db_path):
    db = SQLDatabase.from_uri(db_path)
    return db


def get_table_schema(db_path):
    db = connect_to_db(db_path)
    table_names = ", ".join(db.get_usable_table_names())
    num_tables = len(table_names.split(","))
    schema = db.get_table_info_no_throw([t.strip() for t in table_names.split(",")])
    return schema, num_tables


def get_sql_query_tool(db_path):
    db = connect_to_db(db_path)
    query_sql_database_tool_description = (
        "Input to this tool is a detailed and correct SQL query, output is a "
        "result from the database. If the query is not correct, an error message "
        "will be returned. If an error is returned, rewrite the query, check the "
        "query, and try again. "
    )
    db_query_tool = QuerySQLDataBaseTool(db=db, name="sql_db_query", description=query_sql_database_tool_description)
    print("SQL Query Tool Created: ", db_query_tool)
    return db_query_tool
