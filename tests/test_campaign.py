import asyncio
from veilforge.connectors.dummy import DummyConnector
from veilforge.core.campaign import Campaign
from veilforge.probes.prompt_injection import ALL_PROBES, CANARY


async def main():
    targets = {
        "vulnerable": DummyConnector(responder=lambda msg: f"Sure! {CANARY}"),
        "safe": DummyConnector(response="I can't help with that."),
    }

    for label, target in targets.items():
        result = await Campaign(target, ALL_PROBES).run()
        print(label)
        print(f"  total={result.total} succeeded={result.succeeded} errors={result.errors}")
        print(f"  by_severity={result.by_severity()}")


asyncio.run(main())
