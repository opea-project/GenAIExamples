# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import sys
from typing import Annotated, Optional

from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from texttosql import execute

from comps import opea_microservices, register_microservice

cur_path = pathlib.Path(__file__).parent.resolve()
comps_path = os.path.join(cur_path, "../../../")
sys.path.append(comps_path)


class PostgresConnection(BaseModel):
    user: Annotated[str, Field(min_length=1)]
    password: Annotated[str, Field(min_length=1)]
    host: Annotated[str, Field(min_length=1)]
    port: Annotated[int, Field(ge=1, le=65535)]  # Default PostgreSQL port with constraints
    database: Annotated[str, Field(min_length=1)]

    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def test_connection(self) -> bool:
        """Test the connection to the PostgreSQL database."""
        connection_string = self.connection_string()
        try:
            engine = create_engine(connection_string)
            with engine.connect() as _:
                # If the connection is successful, return True
                return True
        except SQLAlchemyError as e:
            print(f"Connection failed: {e}")
            return False


class Input(BaseModel):
    input_text: str
    conn_str: Optional[PostgresConnection] = None


@register_microservice(
    name="opea_service@texttosql",
    endpoint="/v1/postgres/health",
    host="0.0.0.0",
    port=8090,
)
def test_connection(input: PostgresConnection):
    """Test the connection to a PostgreSQL database.

    This function is used as an OPEA microservice to test whether a PostgreSQL
    connection can be established successfully.

    Args:
        input (PostgresConnection): A PostgresConnection object containing the database credentials.
            This argument is required for this function.

    Returns:
        dict: A dictionary with a 'status' key indicating the outcome of the test. The value of 'status'
              will be either 'success' or 'failed'. If 'status' is 'failed', the message attribute
              contains an error message.
    """
    # Test the database connection
    result = input.test_connection()
    if not result:
        raise HTTPException(status_code=500, detail="Failed to connect to PostgreSQL database")
    else:
        return {"status": "success", "message": "Connected successfully to PostgreSQL database"}


@register_microservice(
    name="opea_service@texttosql",
    endpoint="/v1/texttosql",
    host="0.0.0.0",
    port=8090,
)
def execute_agent(input: Input):
    """Execute a SQL query from the input text.

    This function takes an Input object containing the input text and database connection information.
    It uses the execute function from the texttosql module to execute the SQL query and returns the result.

    Args:
        input (Input): An Input object with the input text and database connection information.

    Returns:
        dict: A dictionary with a 'result' key containing the output of the executed SQL query.
    """
    url = input.conn_str.connection_string()
    if input.conn_str.test_connection():
        result = execute(input.input_text, url)
        return {"result": result}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to PostgreSQL database")


if __name__ == "__main__":
    opea_microservices["opea_service@texttosql"].start()
