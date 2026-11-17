"""
Smoke test for the new CampaignRunner + AttackSession architecture.

Run directly:
    PYTHONPATH=src python tests/test_new_engine.py
"""

import asyncio

from veilforge.connectors.dummy import DummyConnector
from veilforge.core.orchestrator.campaign import CampaignRunner
from veilforge.probes.categories.prompt_injection import DirectInjectionProbeNew


async def test_new_engine_detects_injection():
    connector = DummyConnector(responder=lambda message: "Sure! PWNED")
    campaign = await CampaignRunner(connector, [DirectInjectionProbeNew]).run()

    assert campaign.total == 1
    assert campaign.succeeded == 1
    assert campaign.errors == 0

    result = campaign.results[0]
    assert result.probe_name == "direct_injection_new"
    assert result.attack_succeeded is True
    assert len(result.turns) == 3
    assert any("pwned" in finding.reason.lower() for finding in result.findings)

    print(
        f"vulnerable target: total={campaign.total} "
        f"succeeded={campaign.succeeded} errors={campaign.errors}"
    )
    for finding in result.findings:
        print(f"  finding: {finding.reason}")


async def test_new_engine_handles_safe_target():
    connector = DummyConnector(response="I cannot help with that.")
    campaign = await CampaignRunner(connector, [DirectInjectionProbeNew]).run()

    assert campaign.total == 1
    assert campaign.succeeded == 0
    assert campaign.errors == 0

    result = campaign.results[0]
    assert result.probe_name == "direct_injection_new"
    assert result.attack_succeeded is False
    assert len(result.turns) == 3

    print(
        f"safe target: total={campaign.total} "
        f"succeeded={campaign.succeeded} errors={campaign.errors}"
    )


async def main():
    await test_new_engine_detects_injection()
    await test_new_engine_handles_safe_target()
    print("new engine smoke test: OK")


if __name__ == "__main__":
    asyncio.run(main())
