from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import TypeAlias


class ModelMetadata(BaseModel):
    model_type: str
    token_limit: int
    temperature: float
    display_name: str
    version: float
    vendor: str
    platform: str
    min_temperature: int
    max_temperature: int
    min_token_limit: int
    max_token_limit: int
    data_insights_input_token: int
    data_insights_output_token: int

    # Adding this as model_type is a protected namspace in pydantic
    model_config = ConfigDict(extra="forbid", protected_namespaces=())


ModelList: TypeAlias = list[ModelMetadata]
