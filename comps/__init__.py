#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Document
from comps.cores.proto.docarray import (
    Audio2TextDoc,
    Base64ByteStrDoc,
    DocPath,
    EmbedDoc,
    GeneratedDoc,
    LLMParamsDoc,
    SearchedDoc,
    SearchedMultimodalDoc,
    LVMSearchedMultimodalDoc,
    RerankedDoc,
    TextDoc,
    MetadataTextDoc,
    RAGASParams,
    RAGASScores,
    GraphDoc,
    LVMDoc,
    LVMVideoDoc,
    ImageDoc,
    TextImageDoc,
    MultimodalDoc,
    EmbedMultimodalDoc,
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
    SearchQnAGateway,
    AudioQnAGateway,
    RetrievalToolGateway,
    FaqGenGateway,
    VideoQnAGateway,
    VisualQnAGateway,
    MultimodalQnAGateway,
)

# Telemetry
from comps.cores.telemetry.opea_telemetry import opea_telemetry

# Statistics
from comps.cores.mega.base_statistics import statistics_dict, register_statistics

# Logger
from comps.cores.mega.logger import CustomLogger
