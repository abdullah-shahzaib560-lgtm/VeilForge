# VeilForge Architecture

## Overview

VeilForge is designed as a modular AI red teaming platform.

## Layers

1. **Presentation Layer**
   - CLI (current)
   - Future: Web Dashboard, API

2. **Orchestration Layer**
   - Campaign Manager
   - Result Aggregator

3. **Attack Engine**
   - Probe Library
   - Multi-prompt runners

4. **Network / Privacy Layer**
   - HTTP / SOCKS5 proxy support
   - Future: Proxy chaining, Tor

5. **Connector Layer**
   - Ollama
   - Dummy
   - Future: OpenAI, Anthropic, custom agents

6. **Reporting Layer**
   - JSON reports
   - HTML reports
   - Future: PDF, framework mapping

## Design Principles

- Easy to extend (new probes and connectors)
- Clear separation of concerns
- Useful for both research and practical security testing
