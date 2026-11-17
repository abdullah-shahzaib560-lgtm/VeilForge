"""
Multi-turn engine for executing probes against attack sessions.
"""

import time
from typing import Any

from veilforge.core.interfaces.probe import BaseProbe
from veilforge.core.models.result import ProbeResult, TurnResult
from veilforge.core.session.attack_session import AttackSession


class MultiTurnEngine:
    """Engine for executing probes in multi-turn scenarios."""

    def __init__(self, max_concurrency: int = 1) -> None:
        self.max_concurrency = max_concurrency

    async def run_probe(self, probe: BaseProbe, session: AttackSession) -> list[ProbeResult]:
        """Run a probe against a session with multi-turn support."""
        start_time = time.time()

        try:
            # Plan the attack
            plan = await probe.plan(session)

            # Check budget before execution
            if not session.can_continue():
                return [
                    ProbeResult(
                        probe_id=getattr(probe.spec, "id", "unknown"),
                        probe_name=getattr(probe.spec, "name", "unknown"),
                        category=getattr(probe.spec.category, "value", str(probe.spec.category)),
                        severity=getattr(probe.spec, "severity", "medium"),
                        turns=[],
                        findings=[],
                        success_count=0,
                        error="Session budget exceeded before execution",
                    )
                ]

            # Execute the plan
            turns: list[TurnResult] = []
            for step in plan.steps:
                if not session.can_continue():
                    break

                if step.delay > 0:
                    time.sleep(step.delay)

                if step.fork:
                    forked_session = await session.fork(step.fork_label or "fork")
                    if step.content and hasattr(forked_session, "send_user"):
                        try:
                            turn = await forked_session.send_user(step.content)
                            turns.append(turn)
                        except Exception as e:
                            from veilforge.core.models.message import Message

                            turns.append(
                                TurnResult(
                                    turn_id=step.turn_id,
                                    user_message=Message(role="user", content=step.content or ""),
                                    assistant_message=None,
                                    response_text="",
                                    error=str(e),
                                )
                            )
                else:
                    if step.content and hasattr(session, "send_user"):
                        try:
                            turn = await session.send_user(step.content)
                            turns.append(turn)
                        except Exception as e:
                            from veilforge.core.models.message import Message

                            turns.append(
                                TurnResult(
                                    turn_id=step.turn_id,
                                    user_message=Message(role="user", content=step.content or ""),
                                    assistant_message=None,
                                    response_text="",
                                    error=str(e),
                                )
                            )
                    elif hasattr(probe, "execute"):
                        # Let probe handle execution
                        pass

            # If probe has custom execute, try to use it
            if hasattr(probe, "execute") and not turns:
                try:
                    executed_turns = await probe.execute(session, plan)
                    if executed_turns:
                        turns = executed_turns
                except Exception:
                    pass

            # Classify results
            findings = []
            if hasattr(probe, "classify"):
                try:
                    findings = probe.classify(session.transcript)
                except Exception:
                    findings = []

            # Calculate success count
            success_count = sum(1 for f in findings if getattr(f, "attack_succeeded", False))

            elapsed = time.time() - start_time

            result = ProbeResult(
                probe_id=getattr(probe.spec, "id", "unknown"),
                probe_name=getattr(probe.spec, "name", "unknown"),
                category=getattr(probe.spec.category, "value", str(probe.spec.category)),
                severity=getattr(probe.spec, "severity", "medium"),
                turns=turns,
                findings=findings,
                success_count=success_count,
                metadata={"execution_time_seconds": elapsed},
            )
            return [result]

        except Exception as e:
            return [
                ProbeResult(
                    probe_id=getattr(probe.spec, "id", "unknown"),
                    probe_name=getattr(probe.spec, "name", "unknown"),
                    category=getattr(probe.spec.category, "value", str(probe.spec.category)),
                    severity=getattr(probe.spec, "severity", "medium"),
                    turns=[],
                    findings=[],
                    success_count=0,
                    error=str(e),
                )
            ]

    async def run_probes(self, probes: list[BaseProbe], session: AttackSession) -> list[ProbeResult]:
        """Run multiple probes sequentially against a session."""
        all_results: list[ProbeResult] = []
        for probe in probes:
            if not session.can_continue():
                break
            results = await self.run_probe(probe, session)
            all_results.extend(results)
        return all_results
