from comps import opea_microservices
from llama_index.core.settings import Settings
from edgecraftrag.api.v1 import (
    pipeline,
    data,
    chatqna,
    model
)


if __name__ == "__main__":
    Settings.llm = None

    opea_microservices["opea_service@ec_rag"].start()
