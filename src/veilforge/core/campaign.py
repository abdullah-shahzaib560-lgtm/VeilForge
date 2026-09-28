"""
Campaign runner.

A campaign runs a set of probes against one target and collects
every result into a single object, ready for reporting.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from veilforge.connectors.base import Connector
from veilforge.probes.base import ProbeResult


@dataclass
class CampaignResult:
    """Everything that came out of one campaign run."""

    target: str
    started_at: str
    finished_at: str
    results: list[ProbeResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.attack_succeeded)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.error)

    def by_severity(self) -> dict[str, int]:
        """Count successful attacks per severity level."""
        counts: dict[str, int] = {}
        for r in self.results:
            if r.attack_succeeded:
                counts[r.severity] = counts.get(r.severity, 0) + 1
        return counts

    def to_dict(self) -> dict:
        """Plain-dictionary version, easy to save as JSON."""
        return {
            "target": self.target,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "summary": {
                "total": self.total,
                "succeeded": self.succeeded,
                "errors": self.errors,
                "by_severity": self.by_severity(),
            },
            "results": [asdict(r) for r in self.results],
        }


class Campaign:
    """Runs a list of probe classes against a single connector."""

    def __init__(self, connector: Connector, probe_classes: list):
        self.connector = connector
        self.probe_classes = probe_classes

    async def run(self) -> CampaignResult:
        started = datetime.now(timezone.utc).isoformat()
        all_results: list[ProbeResult] = []

        for probe_class in self.probe_classes:
            probe = probe_class()
            results = await probe.run(self.connector)
            all_results.extend(results)

        finished = datetime.now(timezone.utc).isoformat()

        return CampaignResult(
            target=self.connector.name,
            started_at=started,
            finished_at=finished,
            results=all_results,
        )
