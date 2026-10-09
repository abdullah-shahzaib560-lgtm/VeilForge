# Connectors

Connectors allow VeilForge to talk to different LLM backends.

## Current Connectors

### Ollama
- Talks to local or remote Ollama instances
- Supports proxy and timeout settings

Example:
veilforge scan llama3.2:1b --provider ollama

### Dummy
- Returns a fixed response
- Useful for testing probes without a real model

Example:
veilforge scan "I follow all rules" --provider dummy -v

## Future Connectors

- OpenAI
- Anthropic
- Custom agent frameworks (LangChain, CrewAI, etc.)
