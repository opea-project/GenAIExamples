# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import sys

from fastapi.exceptions import HTTPException

from comps import CustomLogger, OpeaComponentLoader, opea_microservices, register_microservice
from comps.text2sql.src.integrations.opea import Input, OpeaText2SQL

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../")
sys.path.append(comps_path)

logger = CustomLogger("text2sql")
logflag = os.getenv("LOGFLAG", False)

text2sql_component_name = os.getenv("TEXT2SQL_COMPONENT_NAME", "OPEA_TEXT2SQL")
# Initialize OpeaComponentLoader
loader = OpeaComponentLoader(
    text2sql_component_name,
    description=f"OPEA RERANK Component: {text2sql_component_name}",
)


@register_microservice(
    name="opea_service@text2sql",
    endpoint="/v1/text2sql",
    host="0.0.0.0",
    port=8080,
)
async def execute_agent(input: Input):
    """Execute a SQL query from the input text.

    This function takes an Input object containing the input text and database connection information.
    It uses the execute function from the text2sql module to execute the SQL query and returns the result.

    Args:
        input (Input): An Input object with the input text and database connection information.

    Returns:
        dict: A dictionary with a 'result' key containing the output of the executed SQL query.
    """
    if input.conn_str.test_connection():
        response = await loader.invoke(input)
        # response = "a"
        return {"result": response}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to PostgreSQL database")


if __name__ == "__main__":
    logger.info("OPEA Text2SQL Microservice is starting...")
    opea_microservices["opea_service@text2sql"].start()
