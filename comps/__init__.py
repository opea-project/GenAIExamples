#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

# Document
from comps.cores.proto.docarray import (
    Audio2TextDoc,
    Base64ByteStrDoc,
    DocPath,
    EmbedDoc768,
    EmbedDoc1024,
    GeneratedDoc,
    LLMParamsDoc,
    SearchedDoc,
    TextDoc,
)

# Constants
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceRoleType, ServiceType

# Microservice
from comps.cores.mega.orchestrator import ServiceOrchestrator
from comps.cores.mega.orchestrator_with_yaml import ServiceOrchestratorWithYaml
from comps.cores.mega.micro_service import MicroService, register_microservice, opea_microservices
from comps.cores.mega.gateway import Gateway, ChatQnAGateway, CodeGenGateway, CodeTransGateway, DocSumGateway

# Telemetry
from comps.cores.telemetry.opea_telemetry import opea_telemetry
