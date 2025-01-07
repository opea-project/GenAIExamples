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


class OpeaComponentRegistry:
    """Registry class to manage component instances.

    This registry allows storing, retrieving, and managing component instances by their names.
    """

    _registry = {}

    @classmethod
    def register(cls, name):
        """Decorator to register a component class with a specified name.

        :param name: The name to associate with the component class
        :return: Decorator function
        """

        def decorator(component_class):
            if name in cls._registry:
                raise ValueError(f"A component with the name '{name}' is already registered.")
            cls._registry[name] = component_class
            return component_class

        return decorator

    @classmethod
    def get(cls, name):
        """Retrieve a component class by its name.

        :param name: The name of the component class to retrieve
        :return: The component class
        """
        if name not in cls._registry:
            raise KeyError(f"No component found with the name '{name}'.")
        return cls._registry[name]

    @classmethod
    def unregister(cls, name):
        """Remove a component class from the registry by its name.

        :param name: The name of the component class to remove
        """
        if name in cls._registry:
            del cls._registry[name]


class OpeaComponentLoader:
    """Loader class to dynamically load and invoke components.

    This loader retrieves components from the registry and invokes their functionality.
    """

    def __init__(self, component_name, **kwargs):
        """Initialize the loader with a component retrieved from the registry and instantiate it.

        :param component_name: The name of the component to load
        :param kwargs: Additional parameters for the component's initialization
        """
        kwargs["name"] = component_name

        # Retrieve the component class from the registry
        component_class = OpeaComponentRegistry.get(component_name)

        # Instantiate the component with the given arguments
        self.component = component_class(**kwargs)

    async def invoke(self, *args, **kwargs):
        """Invoke the loaded component's execute method.

        :param args: Positional arguments for the invoke method
        :param kwargs: Keyword arguments for the invoke method
        :return: The result of the component's invoke method
        """
        if not hasattr(self.component, "invoke"):
            raise AttributeError(f"The component '{self.component}' does not have an 'invoke' method.")
        return await self.component.invoke(*args, **kwargs)
