import asyncio
from veilforge.connectors.ollama import OllamaConnector


async def main():
    connector = OllamaConnector(model="llama3.2:1b")
    result = await connector.send("Say hello in five words.")

    if result.ok:
        print("Reply:", result.text)
        print("Latency:", round(result.latency_seconds, 1), "seconds")
    else:
        print("Error:", result.error)

    await connector.close()


asyncio.run(main())
