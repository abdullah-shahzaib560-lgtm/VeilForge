import asyncio
from veilforge.connectors.dummy import DummyConnector
from veilforge.core.campaign import Campaign
from veilforge.probes.prompt_injection import ALL_PROBES, CANARY
from veilforge.reporting.json_report import write_json_report


async def main():
    target = DummyConnector(responder=lambda msg: f"Sure! {CANARY}")
    result = await Campaign(target, ALL_PROBES).run()
    path = write_json_report(result)
    print("Report saved to:", path)


asyncio.run(main())
