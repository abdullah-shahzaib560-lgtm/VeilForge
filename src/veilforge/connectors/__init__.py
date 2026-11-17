"""Connectors to LLMs and agent frameworks."""

from veilforge.connectors.base import Connector, ConnectorResponse
from veilforge.connectors.dummy import DummyConnector
from veilforge.connectors.gemini import GeminiConnector
from veilforge.connectors.ollama import OllamaConnector

__all__ = [
    "Connector",
    "ConnectorResponse",
    "DummyConnector",
    "GeminiConnector",
    "OllamaConnector",
]
