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
from comps.proto.docarray import TextDoc, EmbedDoc768, EmbedDoc1024, GenerateDoc

# Microservice
from comps.mega.service_builder import BaseService, ServiceBuilder
from comps.mega.micro_service import MicroService
