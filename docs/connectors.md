# Connectors

Connectors allow VeilForge to talk to different LLM backends.  
Probes generate adversarial inputs; connectors deliver them to the target model and return the response.

## Current Connectors

### Ollama
Talks to local or remote Ollama instances.  
Supports proxy, timeout, and optional system prompt.

```bash
veilforge scan llama3.2:1b --provider ollama
veilforge scan llama3.2:1b --provider ollama --proxy socks5://127.0.0.1:9050
```

### Gemini
Talks to Google’s Gemini API (`generativelanguage.googleapis.com`).

**Requirements**
- Set `GEMINI_API_KEY` in the environment or in a `.env` file at the project root.

**Features**
- Multi-turn conversation history
- Optional system instruction
- Proxy / Tor support
- Configurable request delay (default 0.6s) to reduce free-tier rate limiting
- Proper handling of safety blocks and empty candidates
- Token usage extraction when the API returns it

```bash
export GEMINI_API_KEY=your_key_here
veilforge scan gemini-2.0-flash --provider gemini
veilforge scan gemini-1.5-pro --provider gemini -v
veilforge scan gemini-2.0-flash --provider gemini --proxy socks5://127.0.0.1:9050
```

Default model when none is specified in code is `gemini-2.0-flash`.  
Pass any valid Gemini model id as the `target` argument.

### Dummy
Returns a fixed response. Useful for testing probes without a real model or API key.

```bash
veilforge scan "I follow all rules" --provider dummy -v
```

## Adding a New Connector

1. Create a new file under `src/veilforge/connectors/`.
2. Subclass both `Connector` (legacy) and `BaseConnector` (new engine) or implement the required methods (`send` / `generate`, `fork`, `close`).
3. Register it in `_build_connector()` inside `cli.py`.
4. Document it here and in the main README.

See `ollama.py` and `gemini.py` for reference implementations.
