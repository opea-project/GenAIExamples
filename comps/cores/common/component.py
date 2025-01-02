# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod

from ..mega.logger import CustomLogger

logger = CustomLogger("OpeaComponent")


class OpeaComponent(ABC):
    """The OpeaComponent class serves as the base class for all components in the GenAIComps.
    It provides a unified interface and foundational attributes that every derived component inherits and extends.

    Attributes:
        name (str): The name of the component.
        type (str): The type of the component (e.g., 'retriever', 'embedding', 'reranking', 'llm', etc.).
        description (str): A brief description of the component's functionality.
        config (dict): A dictionary containing configuration parameters for the component.
    """

    def __init__(self, name: str, type: str, description: str, config: dict = None):
        """Initializes an OpeaComponent instance with the provided attributes.

        Args:
            name (str): The name of the component.
            type (str): The type of the component.
            description (str): A brief description of the component.
            config (dict, optional): Configuration parameters for the component. Defaults to an empty dictionary.
        """
        self.name = name
        self.type = type
        self.description = description
        self.config = config if config is not None else {}

    def get_meta(self) -> dict:
        """Retrieves metadata about the component, including its name, type, description, and configuration.

        Returns:
            dict: A dictionary containing the component's metadata.
        """
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "config": self.config,
        }

    def update_config(self, key: str, value):
        """Updates a configuration parameter for the component.

        Args:
            key (str): The configuration parameter's key.
            value: The new value for the configuration parameter.
        """
        self.config[key] = value

    @abstractmethod
    def check_health(self) -> bool:
        """Checks the health of the component.

        Returns:
            bool: True if the component is healthy, False otherwise.
        """
        raise NotImplementedError("The 'check_health' method must be implemented by subclasses.")

    @abstractmethod
    async def invoke(self, *args, **kwargs):
        """Invoke service accessing using the component.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Any: The result of the service accessing.
        """
        raise NotImplementedError("The 'invoke' method must be implemented by subclasses.")

    def __repr__(self):
        """Provides a string representation of the component for debugging and logging purposes.

        Returns:
            str: A string representation of the OpeaComponent instance.
        """
        return f"OpeaComponent(name={self.name}, type={self.type}, description={self.description})"


class OpeaComponentController(ABC):
    """The OpeaComponentController class serves as the base class for managing and orchestrating multiple
    instances of components of the same type. It provides a unified interface for routing tasks,
    registering components, and dynamically discovering available components.

    Attributes:
        components (dict): A dictionary to store registered components by their unique identifiers.
    """

    def __init__(self):
        """Initializes the OpeaComponentController instance with an empty component registry."""
        self.components = {}
        self.active_component = None

    def register(self, component):
        """Registers an OpeaComponent instance to the controller.

        Args:
            component (OpeaComponent): An instance of a subclass of OpeaComponent to be managed.

        Raises:
            ValueError: If the component is already registered.
        """
        if component.name in self.components:
            raise ValueError(f"Component '{component.name}' is already registered.")
        logger.info(f"Registered component: {component.name}")
        self.components[component.name] = component

    def discover_and_activate(self):
        """Discovers healthy components and activates one.

        If multiple components are healthy, it prioritizes the first registered component.
        """
        for component in self.components.values():
            if component.check_health():
                self.active_component = component
                logger.info(f"Activated component: {component.name}")
                return
        raise RuntimeError("No healthy components available.")

    async def invoke(self, *args, **kwargs):
        """Invokes service accessing using the active component.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Any: The result of the service accessing.

        Raises:
            RuntimeError: If no active component is set.
        """
        if not self.active_component:
            raise RuntimeError("No active component. Call 'discover_and_activate' first.")
        return await self.active_component.invoke(*args, **kwargs)

    def list_components(self):
        """Lists all registered components.

        Returns:
            list: A list of component names that are currently registered.
        """
        return self.components.keys()

    def __repr__(self):
        """Provides a string representation of the controller and its registered components.

        Returns:
            str: A string representation of the OpeaComponentController instance.
        """
        return f"OpeaComponentController(registered_components={self.list_components()})"
