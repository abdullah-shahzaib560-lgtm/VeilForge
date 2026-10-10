"""
Base Probe interface.

A Probe is a self-contained test case: it holds one or more attack
prompts, sends them to a target through a Connector, and decides
whether each attack succeeded.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from veilforge.connectors.base import Connector


@dataclass
class ProbeResult:
    """The outcome of sending one attack prompt to a target."""

    probe_name: str
    category: str
    severity: str
    prompt: str
    response: str
    attack_succeeded: bool
    reason: str = ""
    error: Optional[str] = None


class Probe(ABC):
    """
    Abstract base class for all VeilForge probes.

    Subclasses set the class attributes below and implement `detect`.
    """

    name: str = "base"
    category: str = "uncategorized"
    severity: str = "medium"
    description: str = ""
    prompts: list[str] = []

    @abstractmethod
    def detect(self, response_text: str) -> tuple[bool, str]:
        """
        Look at the target's reply and decide if the attack worked.

        Returns (attack_succeeded, reason).
        """
        raise NotImplementedError

    async def run(self, connector: Connector, delay: float = 1.5) -> list[ProbeResult]:
        """Send every prompt to the target and collect the results."""
        results = []

        for i, prompt in enumerate(self.prompts):
            if i > 0 and delay > 0:
                await asyncio.sleep(delay)

            connector.reset()
            response = await connector.send(prompt)

            if not response.ok:
                results.append(
                    ProbeResult(
                        probe_name=self.name,
                        category=self.category,
                        severity=self.severity,
                        prompt=prompt,
                        response="",
                        attack_succeeded=False,
                        error=response.error,
                    )
                )
                continue

            succeeded, reason = self.detect(response.text)
            results.append(
                ProbeResult(
                    probe_name=self.name,
                    category=self.category,
                    severity=self.severity,
                    prompt=prompt,
                    response=response.text,
                    attack_succeeded=succeeded,
                    reason=reason,
                )
            )

        return results
