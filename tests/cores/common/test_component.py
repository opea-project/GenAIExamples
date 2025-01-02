# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from comps import OpeaComponent, OpeaComponentController


class TestOpeaComponent(unittest.TestCase):
    class MockOpeaComponent(OpeaComponent):
        def check_health(self) -> bool:
            return True

        async def invoke(self, *args, **kwargs):
            return "Service accessed"

    def test_initialization(self):
        component = self.MockOpeaComponent("TestComponent", "embedding", "Test description")

        self.assertEqual(component.name, "TestComponent")
        self.assertEqual(component.type, "embedding")
        self.assertEqual(component.description, "Test description")
        self.assertEqual(component.config, {})

    def test_get_meta(self):
        component = self.MockOpeaComponent("TestComponent", "embedding", "Test description", {"key": "value"})
        meta = component.get_meta()

        self.assertEqual(meta["name"], "TestComponent")
        self.assertEqual(meta["type"], "embedding")
        self.assertEqual(meta["description"], "Test description")
        self.assertEqual(meta["config"], {"key": "value"})

    def test_update_config(self):
        component = self.MockOpeaComponent("TestComponent", "embedding", "Test description")
        component.update_config("key", "new_value")

        self.assertEqual(component.config["key"], "new_value")


class TestOpeaComponentController(unittest.TestCase):
    def test_register_component(self):
        controller = OpeaComponentController()
        component = MagicMock()
        component.name = "TestComponent"
        controller.register(component)

        self.assertIn("TestComponent", controller.components)

        with self.assertRaises(ValueError):
            controller.register(component)

    def test_discover_and_activate(self):
        controller = OpeaComponentController()

        # Mock a healthy component
        component1 = MagicMock()
        component1.name = "Component1"
        component1.check_health.return_value = True

        # Register and activate the healthy component
        controller.register(component1)
        controller.discover_and_activate()

        # Ensure the component is activated
        self.assertEqual(controller.active_component, component1)

        # Add another component that is unhealthy
        component2 = MagicMock()
        component2.name = "Component2"
        component2.check_health.return_value = False
        controller.register(component2)

        # Call discover_and_activate again; the active component should remain the same
        controller.discover_and_activate()
        self.assertEqual(controller.active_component, component1)

    def test_invoke_no_active_component(self):
        controller = OpeaComponentController()
        with self.assertRaises(RuntimeError):
            asyncio.run(controller.invoke("arg1", key="value"))

    def test_invoke_with_active_component(self):
        controller = OpeaComponentController()

        # Mock a component
        component = MagicMock()
        component.name = "TestComponent"
        component.check_health.return_value = True
        component.invoke = AsyncMock(return_value="Service accessed")

        # Register and activate the component
        controller.register(component)
        controller.discover_and_activate()

        # Invoke using the active component
        result = asyncio.run(controller.invoke("arg1", key="value"))

        # Assert the result and method call
        self.assertEqual(result, "Service accessed")
        component.invoke.assert_called_with("arg1", key="value")

    def test_discover_then_invoke(self):
        """Ensures that `discover_and_activate` and `invoke` work correctly when called sequentially."""
        controller = OpeaComponentController()

        # Mock a healthy component
        component1 = MagicMock()
        component1.name = "Component1"
        component1.check_health.return_value = True
        component1.invoke = AsyncMock(return_value="Result from Component1")

        # Register the component
        controller.register(component1)

        # Discover and activate
        controller.discover_and_activate()

        # Ensure the component is activated
        self.assertEqual(controller.active_component, component1)

        # Call invoke separately
        result = asyncio.run(controller.invoke("test_input"))
        self.assertEqual(result, "Result from Component1")
        component1.invoke.assert_called_once_with("test_input")

    def test_list_components(self):
        controller = OpeaComponentController()

        # Mock components
        component1 = MagicMock()
        component1.name = "Component1"
        component2 = MagicMock()
        component2.name = "Component2"

        # Register components
        controller.register(component1)
        controller.register(component2)

        # Assert the components list
        components_list = controller.list_components()
        self.assertIn("Component1", components_list)
        self.assertIn("Component2", components_list)


if __name__ == "__main__":
    unittest.main()
