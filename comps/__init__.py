#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

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
    RAGASParams,
    RAGASScores,
    LVMDoc,
)

# Constants
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceRoleType, ServiceType

# Microservice
from comps.cores.mega.orchestrator import ServiceOrchestrator
from comps.cores.mega.orchestrator_with_yaml import ServiceOrchestratorWithYaml
from comps.cores.mega.micro_service import MicroService, register_microservice, opea_microservices
from comps.cores.mega.gateway import (
    Gateway,
    ChatQnAGateway,
    CodeGenGateway,
    CodeTransGateway,
    DocSumGateway,
    TranslationGateway,
)

# Telemetry
from comps.cores.telemetry.opea_telemetry import opea_telemetry

# Statistics
from comps.cores.mega.base_statistics import statistics_dict, register_statistics
