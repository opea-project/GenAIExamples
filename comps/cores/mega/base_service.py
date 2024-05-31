# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import abc
from types import SimpleNamespace
from typing import TYPE_CHECKING, Dict, Optional

from .logger import CustomLogger

__all__ = ["BaseService"]


class BaseService:
    """BaseService creates an HTTP/gRPC server as a microservice."""

    def __init__(
        self,
        name: Optional[str] = "Base service",
        runtime_args: Optional[Dict] = {},
        **kwargs,
    ):
        """Initialize the BaseService with a name, runtime arguments, and any additional arguments."""
        self.name = name
        self.runtime_args = runtime_args
        self._process_runtime_args()
        self.title = self.runtime_args.title
        self.description = self.runtime_args.description
        self.logger = CustomLogger(self.name)
        self.server = None

    def _process_runtime_args(self):
        """Process the runtime arguments to ensure they are in the correct format."""
        _runtime_args = self.runtime_args if isinstance(self.runtime_args, dict) else vars(self.runtime_args)
        self.runtime_args = SimpleNamespace(**_runtime_args)

    @property
    def primary_port(self):
        """Gets the first port of the port list argument.

        :return: The first port to be exposed
        """
        return self.runtime_args.port[0] if isinstance(self.runtime_args.port, list) else self.runtime_args.port

    @property
    def all_ports(self):
        """Gets all the list of ports from the runtime_args as a list.

        :return: The lists of ports to be exposed
        """
        return self.runtime_args.port if isinstance(self.runtime_args.port, list) else [self.runtime_args.port]

    @property
    def protocols(self):
        """Gets all the list of protocols from the runtime_args as a list.

        :return: The lists of protocols to be exposed
        """
        return (
            self.runtime_args.protocol if isinstance(self.runtime_args.protocol, list) else [self.runtime_args.protocol]
        )

    @property
    def host_address(self):
        """Gets the host from the runtime_args
        :return: The host where to bind the gateway."""
        return self.runtime_args.host or "127.0.0.1"

    @abc.abstractmethod
    async def initialize_server(self):
        """Abstract method to setup the server.

        This should be implemented in the child class.
        """
        ...

    @abc.abstractmethod
    async def execute_server(self):
        """Abstract method to run the server indefinitely.

        This should be implemented in the child class.
        """
        ...

    @abc.abstractmethod
    async def terminate_server(self):
        """Abstract method to shutdown the server and free other allocated resources, e.g, health check service, etc.

        This should be implemented in the child class.
        """
        ...

    @staticmethod
    def check_server_readiness(
        ctrl_address: str,
        protocol: Optional[str] = "http",
        **kwargs,
    ) -> bool:
        """Check if server status is ready.

        :param ctrl_address: the address where the control request needs to be sent.
        :param protocol: protocol of the service.
        :param kwargs: extra keyword arguments.
        :return: True if status is ready else False.
        """
        from http_service import HTTPService

        res = False
        if protocol is None or protocol == "http":
            res = HTTPService.check_readiness(ctrl_address)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
        return res

    @staticmethod
    async def async_check_server_readiness(
        ctrl_address: str,
        protocol: Optional[str] = "grpc",
        **kwargs,
    ) -> bool:
        """Asynchronously check if server status is ready.

        :param ctrl_address: the address where the control request needs to be sent.
        :param protocol: protocol of the service.
        :param kwargs: extra keyword arguments.
        :return: True if status is ready else False.
        """
        if TYPE_CHECKING:
            from http_service import HTTPService
        res = False
        if protocol is None or protocol == "http":
            res = await HTTPService.async_check_readiness(ctrl_address)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
        return res
