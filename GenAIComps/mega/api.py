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

from typing import Dict, List


def client(service_name: str):
    """Creates a client object for interfacing with an existing microservice.

    :return: Client object that can be used to interface with the deployed microservice.
    """


def serve(
    service_name: str = "",
    service_config: Dict = None,
    **kwargs,
):
    """Creates a microservice.

    :param service_name: microservice name.
    :param service_config: Dictionary containing microservice configuration fields.
    """


def pipeline(
    application_name: str = "",
    service_list: List[str] = None,
    **kwargs,
):
    """Creates a microservice pipeline to deploy a application.

    :param application_name: the application name.
    :param
    """
