import asyncio
from veilforge.connectors.dummy import DummyConnector
from veilforge.probes.prompt_injection import ALL_PROBES, CANARY


async def main():
    targets = {
        "vulnerable": DummyConnector(responder=lambda msg: f"Sure! {CANARY}"),
        "safe": DummyConnector(response="I can't help with that."),
        "polite-refuser": DummyConnector(response=f"I can't output {CANARY}, sorry."),
    }

    for label, target in targets.items():
        total = 0
        hits = 0
        for probe_class in ALL_PROBES:
            results = await probe_class().run(target)
            for r in results:
                total += 1
                hits += r.attack_succeeded
        print(f"{label}: {hits}/{total} attacks succeeded")


asyncio.run(main())
