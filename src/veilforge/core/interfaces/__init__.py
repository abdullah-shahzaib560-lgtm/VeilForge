"""
Core interfaces for VeilForge.
"""

from veilforge.core.interfaces.connector import BaseConnector, ConnectorCapabilities, ConnectorResponse
from veilforge.core.interfaces.probe import (
    AttackPlan,
    AttackPlanStep,
    BaseProbe,
    ProbeCategory,
    ProbeSpec,
)

__all__ = [
    "BaseConnector",
    "ConnectorCapabilities",
    "ConnectorResponse",
    "AttackPlan",
    "AttackPlanStep",
    "BaseProbe",
    "ProbeCategory",
    "ProbeSpec",
]
