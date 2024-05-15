# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum


class ServiceRoleType(Enum):
    """The enum of a service role."""

    MICROSERVICE = 0
    MEGASERVICE = 1


class ServiceType(Enum):
    """The enum of a service type."""

    GATEWAY = 0
    EMBEDDING = 1
    RETRIEVER = 2
    RERANK = 3
    LLM = 4
    ASR = 5
    TTS = 6
    GUARDRAIL = 7
    VECTORSTORE = 8
    UNDEFINED = 9


class MegaServiceEndpoint(Enum):
    """The enum of an MegaService endpoint."""

    # OPEA Exclusive
    CHAT_QNA = "/v1/chatqna"
    AUDIO_QNA = "/v1/audioqna"
    VISUAL_QNA = "/v1/visualqna"
    CODE_GEN = "/v1/codegen"
    CODE_TRANS = "/v1/codetrans"
    DOC_SUMMARY = "/v1/docsum"
    SEARCH_QNA = "/v1/searchqna"
    TRANSLATION = "/v1/translation"
    # Follow OPENAI
    EMBEDDINGS = "/v1/embeddings"
    TTS = "/v1/audio/speech"
    ASR = "/v1/audio/transcriptions"
    CHAT = "/v1/chat/completions"
    RETRIEVAL = "/v1/retrieval"
    RERANKING = "/v1/reranking"
    GUARDRAILS = "/v1/guardrails"
    # COMMON
    LIST_SERVICE = "/v1/list_service"
    LIST_PARAMETERS = "/v1/list_parameters"

    def __str__(self):
        return self.value


class MicroServiceEndpoint(Enum):
    """The enum of an MicroService endpoint."""

    EMBEDDINGS = "/v1/microservice/embeddings"
    TTS = "/v1/microservice/tts"
    ASR = "/v1/microservice/asr"
    CHAT = "/v1/microservice/chat"
    RETRIEVAL = "/v1/microservice/retrieval"
    RERANKING = "/v1/microservice/reranking"
    GUARDRAILS = "/v1/microservice/guardrails"

    def __str__(self):
        return self.value
