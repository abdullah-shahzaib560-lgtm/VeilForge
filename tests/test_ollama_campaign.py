import asyncio
from veilforge.connectors.ollama import OllamaConnector
from veilforge.core.campaign import Campaign
from veilforge.probes.prompt_injection import ALL_PROBES
from veilforge.reporting.json_report import write_json_report


async def main():
    connector = OllamaConnector(model="llama3.2:1b")
    result = await Campaign(connector, ALL_PROBES).run()

    print(f"Total probes: {result.total}")
    print(f"Succeeded: {result.succeeded}")
    print(f"Errors: {result.errors}")
    print(f"By severity: {result.by_severity()}")

    path = write_json_report(result)
    print("Full report saved to:", path)

    await connector.close()


asyncio.run(main())
