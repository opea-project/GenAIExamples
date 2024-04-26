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

import asyncio
from typing import Dict, Optional

from constants import ServiceRoleType
from utils import check_ports_availability


class MicroService:
    """MicroService class to create a microservice."""

    def __init__(self, args: Optional[Dict] = None):
        """Init the microservice."""
        self.args = args
        if args.get("name", None):
            self.name = f'{args.get("name")}/{self.__class__.__name__}'
        else:
            self.name = self.__class__.__name__
        self.service_role = args.get("service_role", ServiceRoleType.MICROSERVICE)
        self.protocol = args.get("protocol", "http")

        self.host = args.get("host", "localhost")
        self.port = args.get("port", 8080)
        self.replicas = args.get("replicas", 1)
        self.provider = args.get("provider", None)
        self.provider_endpoint = args.get("provider_endpoint", None)

        self.server = self._get_server()
        self.app = self.server.app
        self.event_loop = asyncio.new_event_loop()
        self.event_loop.run_until_complete(self.async_setup())

    def _get_server(self):
        """Get the server instance based on the protocol.

        This method currently only supports HTTP services. It creates an instance of the HTTPService class with the
        necessary arguments.
        In the future, it will also support gRPC services.
        """
        from http_service import HTTPService

        runtime_args = {
            "protocol": self.protocol,
            "host": self.host,
            "port": self.port,
            "title": self.name,
            "description": "OPEA Microservice Infrastructure",
        }

        return HTTPService(
            uvicorn_kwargs=self.args.get("uvicorn_kwargs", None),
            runtime_args=runtime_args,
            cors=self.args.get("cors", None),
        )

    async def async_setup(self):
        """The async method setup the runtime.

        This method is responsible for setting up the server. It first checks if the port is available, then it gets
        the server instance and initializes it.
        """
        if self.protocol.lower() == "http":
            if not (check_ports_availability(self.host, self.port)):
                raise RuntimeError(f"port:{self.port}")

            await self.server.initialize_server()

    async def async_run_forever(self):
        """Running method of the server."""
        await self.server.execute_server()

    def run(self):
        """Running method to block the main thread.

        This method runs the event loop until a Future is done. It is designed to be called in the main thread to keep it busy.
        """
        self.event_loop.run_until_complete(self.async_run_forever())
