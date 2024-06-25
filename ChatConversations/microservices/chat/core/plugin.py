from typing import Protocol, Any


class PluginFactory(Protocol):
    def register(type: str, obj: Any) -> None:
        """Factory classes implement this low-level method to store plugins in a dict."""
        ...


class Plugin(Protocol):
    def register_plugin(self, factory: PluginFactory) -> None:
        """Plugin classes implement this method to register the plugin."""
        ...
