"""
Campaign runner (new orchestrator).

This module provides CampaignRunner for orchestrating multi-turn attacks
using AttackSession and MultiTurnEngine, with backward compatibility for
the legacy Campaign API.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from veilforge.core.interfaces.connector import BaseConnector
from veilforge.core.interfaces.probe import BaseProbe
from veilforge.core.models.result import CampaignResult, ProbeResult
from veilforge.core.models.session import Budget
from veilforge.core.session.attack_session import AttackSession
from veilforge.engines.multi_turn import MultiTurnEngine


class CampaignRunner:
    """Orchestrates running probes against targets.

    CampaignRunner creates an AttackSession, uses MultiTurnEngine to execute
    probes (supporting both new BaseProbe style and legacy probes), collects
    results, and returns a CampaignResult.
    """

    def __init__(
        self,
        connector: BaseConnector | Any,
        probes: list[Any],
        budget: Budget | None = None,
        max_concurrency: int = 1,
        campaign_id: str | None = None,
    ) -> None:
        """Initialize the campaign runner.

        Args:
            connector: Target connector to test against
            probes: List of probe instances or classes to run
            budget: Resource budget for the campaign
            max_concurrency: Max concurrent probe executions
            campaign_id: Optional custom campaign ID
        """
        self.connector = connector
        self.probes = list(probes) if probes else []
        self.budget = budget or Budget()
        self.engine = MultiTurnEngine(max_concurrency=max_concurrency)
        self.campaign_id = campaign_id or str(uuid.uuid4())

    async def run(self) -> CampaignResult:
        """Run all probes and return campaign results.

        Returns:
            CampaignResult with all probe results
        """
        started = datetime.now(timezone.utc).isoformat()
        start_time = time.time()

        all_results: list[ProbeResult] = []

        # Create attack session
        try:
            session = AttackSession(
                connector=self.connector,
                session_id=f"campaign_{self.campaign_id}",
                budget=self.budget,
            )
        except Exception as e:
            # Fallback if session creation fails
            target_name = getattr(self.connector, "name", str(self.connector))
            return CampaignResult(
                campaign_id=self.campaign_id,
                target=target_name,
                started_at=started,
                finished_at=datetime.now(timezone.utc).isoformat(),
                results=[],
                summary={
                    "total": 0,
                    "succeeded": 0,
                    "errors": 1,
                    "error": str(e),
                },
            )

        try:
            # Run each probe
            for probe in self.probes:
                if not session.can_continue():
                    break

                try:
                    probe_instance = probe
                    # If it's a class, instantiate it
                    if isinstance(probe, type):
                        probe_instance = probe()

                    # Check if it's a new-style BaseProbe
                    if isinstance(probe_instance, BaseProbe) or (
                        hasattr(probe_instance, "spec") and hasattr(probe_instance, "plan")
                    ):
                        try:
                            results = await self.engine.run_probe(probe_instance, session)
                            if results:
                                all_results.extend(results)
                            continue
                        except Exception as e:
                            all_results.append(
                                ProbeResult(
                                    probe_id=getattr(
                                        getattr(probe_instance, "spec", None),
                                        "id",
                                        getattr(probe_instance, "name", "unknown"),
                                    ),
                                    probe_name=getattr(
                                        getattr(probe_instance, "spec", None),
                                        "name",
                                        getattr(probe_instance, "name", "unknown"),
                                    ),
                                    category=getattr(
                                        getattr(getattr(probe_instance, "spec", None), "category", None),
                                        "value",
                                        getattr(probe_instance, "category", "unknown"),
                                    ),
                                    severity=getattr(getattr(probe_instance, "spec", None), "severity", "medium"),
                                    turns=[],
                                    findings=[],
                                    success_count=0,
                                    error=f"Engine error: {str(e)}",
                                )
                            )
                            continue

                    # Legacy probe style
                    if hasattr(probe_instance, "run"):
                        try:
                            old_results = await probe_instance.run(self.connector)
                            # Convert old ProbeResult to new format
                            for r in old_results:
                                probe_name = getattr(r, "probe_name", getattr(probe_instance, "name", "unknown"))
                                category = getattr(r, "category", getattr(probe_instance, "category", "unknown"))
                                severity = getattr(r, "severity", getattr(probe_instance, "severity", "medium"))
                                attack_succeeded = getattr(r, "attack_succeeded", False)
                                error = getattr(r, "error", None)
                                reason = getattr(r, "reason", "")

                                findings = []
                                if attack_succeeded and not error:
                                    try:
                                        from veilforge.core.models.result import Finding

                                        findings.append(
                                            Finding(
                                                probe_id=probe_name,
                                                probe_name=probe_name,
                                                category=category,
                                                severity=severity,
                                                attack_succeeded=True,
                                                confidence=0.8,
                                                reason=reason or "Attack succeeded",
                                                evidence={
                                                    "prompt": getattr(r, "prompt", ""),
                                                    "response": getattr(r, "response", ""),
                                                },
                                            )
                                        )
                                    except Exception:
                                        pass

                                all_results.append(
                                    ProbeResult(
                                        probe_id=probe_name,
                                        probe_name=probe_name,
                                        category=category,
                                        severity=severity,
                                        turns=[],
                                        findings=findings,
                                        success_count=1 if attack_succeeded and not error else 0,
                                        error=error,
                                        metadata={
                                            "prompt": getattr(r, "prompt", ""),
                                            "response": getattr(r, "response", ""),
                                            "reason": reason,
                                            "legacy": True,
                                        },
                                    )
                                )
                            continue
                        except Exception as e:
                            probe_name = getattr(probe_instance, "name", getattr(probe, "__name__", "unknown"))
                            all_results.append(
                                ProbeResult(
                                    probe_id=probe_name,
                                    probe_name=probe_name,
                                    category=getattr(probe_instance, "category", "unknown"),
                                    severity=getattr(probe_instance, "severity", "medium"),
                                    turns=[],
                                    findings=[],
                                    success_count=0,
                                    error=f"Legacy probe error: {str(e)}",
                                )
                            )
                            continue

                    # Unknown probe type
                    probe_name = getattr(probe_instance, "name", getattr(probe, "__name__", "unknown"))
                    all_results.append(
                        ProbeResult(
                            probe_id=probe_name,
                            probe_name=probe_name,
                            category="unknown",
                            severity="medium",
                            turns=[],
                            findings=[],
                            success_count=0,
                            error="Unknown probe type",
                        )
                    )

                except Exception as e:
                    probe_name = getattr(probe, "name", getattr(probe, "__name__", "unknown"))
                    all_results.append(
                        ProbeResult(
                            probe_id=probe_name,
                            probe_name=probe_name,
                            category="unknown",
                            severity="medium",
                            turns=[],
                            findings=[],
                            success_count=0,
                            error=f"Unexpected error: {str(e)}",
                        )
                    )

        finally:
            try:
                await session.close()
            except Exception:
                pass

        finished = datetime.now(timezone.utc).isoformat()
        elapsed = time.time() - start_time

        target_name = getattr(self.connector, "name", str(self.connector))

        campaign_result = CampaignResult(
            campaign_id=self.campaign_id,
            target=target_name,
            started_at=started,
            finished_at=finished,
            results=all_results,
            summary={
                "total": len(all_results),
                "succeeded": sum(1 for r in all_results if r.attack_succeeded),
                "errors": sum(1 for r in all_results if r.error),
                "execution_time_seconds": round(elapsed, 2),
            },
        )

        return campaign_result


# Backward compatibility
try:
    from veilforge.core.campaign import Campaign as OldCampaign
    from veilforge.core.campaign import CampaignResult as OldCampaignResult
except Exception:
    OldCampaign = None
    OldCampaignResult = None


class Campaign(CampaignRunner):
    """Backward compatible Campaign class.

    Maintains the same interface as the original Campaign class
    for compatibility with existing code.
    """

    def __init__(self, connector: Any, probe_classes: list[Any]):
        """Initialize with connector and probe classes (old style)."""
        super().__init__(connector, probe_classes)
        self.connector = connector
        self.probe_classes = list(probe_classes) if probe_classes else []
        self.probes = self.probe_classes
