import re
from pydantic import BaseModel, AfterValidator, BeforeValidator, ConfigDict
from typing import TypeAlias, Annotated, Generic, TypeVar

alpha_numperic_pattern: str = r"^[a-zA-Z_0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9_]$"

def validate_alpha_num_extended(val: str):
    match = re.match(alpha_numperic_pattern, val)
    assert match is not None, f"Invalid or unsupported value."
    return val

AlphaNumericString: TypeAlias = Annotated[
    str, AfterValidator(validate_alpha_num_extended)
]

MongoObjectId: TypeAlias = Annotated[str, BeforeValidator(str)]

# Generic template for API response wrapper
T = TypeVar("T")

class ConversationServiceResponseWrapper(BaseModel, Generic[T]):
    data: T

    model_config = ConfigDict(extra="forbid")