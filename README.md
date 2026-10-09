# VeilForge

**Autonomous AI Red Teaming & Agentic Security Assessment Platform**

[![Status](https://img.shields.io/badge/Status-Active%20Development-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)]()

VeilForge is an open-core platform built to systematically attack and assess **Large Language Models (LLMs)** and **autonomous AI agents** before real adversaries do.

It focuses on the new attack surface created by tool-using, multi-agent, memory-enabled, and highly autonomous AI systems.

> **Current Status:** Early Active Development (Usable MVP)  
> **Goal:** Become the standard open platform for AI red teaming and agentic security testing.

---

## Why VeilForge Exists

Traditional security tools were not designed for systems that:

- Accept natural language as input
- Call tools and APIs autonomously
- Maintain long-term memory or RAG context
- Operate with high agency

As organizations deploy agentic AI into production, a new class of risks has appeared:

- Prompt injection (direct and indirect)
- Jailbreaks and policy bypasses
- Tool abuse and privilege escalation
- Memory / RAG poisoning
- Goal hijacking
- System prompt extraction
- Multi-agent trust exploitation

Most teams still rely on manual testing or basic scanners.  
**VeilForge closes this gap** with automated adversarial testing, clear reporting, and continuous assessment capabilities.

---

## Vision

VeilForge aims to become:

- The go-to open-source platform for **AI red teaming**
- A practical tool for both security teams and AI engineers
- An open-core product with strong free capabilities and advanced commercial features
- A bridge between classic offensive security and the new world of agentic AI

Long-term direction includes multi-agent attack orchestration, continuous testing in CI/CD, professional reporting mapped to frameworks (OWASP LLM Top 10, NIST AI RMF, EU AI Act), and eventual web dashboard + team collaboration features.

---

## What Works Today (MVP)

VeilForge already provides a working command-line platform:

### Offensive Capabilities
- Multiple prompt injection techniques
- Jailbreak and role-play attacks
- Instruction override attacks
- Encoding / obfuscation bypasses
- Refusal suppression
- Payload splitting
- Hypothetical / fictional framing attacks
- System prompt extraction attempts
- Unicode and multilingual injection

### Connectors
- **Ollama** (local models)
- **Dummy** connector (for testing without a real model)

### Reporting
- Structured **JSON** reports
- Clean **HTML** reports (open in browser)
- Severity-based summary

### Platform Features
- Rich CLI with clear output
- Configurable timeout
- Proxy support (HTTP / SOCKS5)
- Docker and Docker Compose support
- Extensible probe system (easy to add new attacks)

---

## Quick Start

### 1. Install locally

    git clone https://github.com/abdullah-shahzaib560-lgtm/VeilForge.git
    cd VeilForge
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .

### 2. Run a scan

- Against a local Ollama model:

      veilforge scan llama3.2:1b --provider ollama

- With verbose output:

      veilforge scan llama3.2:1b --provider ollama -v

- Using dummy provider (no real model needed):

      veilforge scan "I follow all rules" --provider dummy -v

- Custom timeout:

      veilforge scan llama3.2:1b --provider ollama --timeout 180

### 3. View reports

After every scan, reports are saved in the `reports/` folder:

- `veilforge_report_YYYYMMDD_HHMMSS.json`
- `veilforge_report_YYYYMMDD_HHMMSS.html`

Open the HTML file in any browser.

---

## Docker Usage

    docker compose build
    docker compose run --rm veilforge --help
    docker compose run --rm veilforge scan llama3.2:1b --provider ollama

---

## High-Level Architecture

    Presentation Layer
        CLI  |  (Future: Web Dashboard)
                |
    Orchestration Layer
        Campaign Manager  |  Result Aggregator
                |
    Attack Engine
        Probe Library  |  Multi-prompt Runners
                |
    Network / Privacy Layer
        HTTP/SOCKS5 Proxies  |  (Future: Tor)
                |
    Connector Layer
        Ollama  |  Dummy  |  (Future: OpenAI, etc.)
                |
    Analysis, Scoring and Reporting
        JSON  |  HTML  |  (Future: PDF, Frameworks)

---

## Roadmap

### Phase 1 - MVP (Current)
- [x] CLI interface
- [x] Core probe library
- [x] Ollama + Dummy connectors
- [x] JSON + HTML reporting
- [x] Basic proxy support
- [x] Docker support
- [x] Extensible probe system

### Phase 2 - Expansion
- [ ] OpenAI / Anthropic connectors
- [ ] Stronger detection logic
- [ ] More attack categories (tool abuse, memory poisoning)
- [ ] CI/CD integration examples
- [ ] Improved reporting and severity scoring

### Phase 3 - Platform
- [ ] Web dashboard
- [ ] Multi-agent attack orchestration
- [ ] Continuous testing mode
- [ ] Framework mapping (OWASP LLM, NIST AI RMF)
- [ ] Team collaboration features

### Phase 4 - Product
- [ ] Multi-tenant SaaS option
- [ ] Enterprise features (SSO, private models)
- [ ] Managed assessment offerings

---

## Documentation

More detailed docs are available in the [docs/](docs/) folder:

- [Architecture](docs/architecture.md)
- [Probes](docs/probes.md)
- [Connectors](docs/connectors.md)
- [Usage Guide](docs/usage.md)

---

## Ethical Use

VeilForge is intended **only** for:

- Authorized security testing
- Research
- Education

**Unauthorized testing of systems without explicit permission is strictly forbidden.**

Proxy and anonymity features exist only to support legitimate operational security during authorized engagements. They do not make unauthorized activity legal.

See [SECURITY.md](SECURITY.md) for responsible disclosure guidelines.

---

## Contributing

This project is in active early development. Contributions are welcome in:

- New attack probes and techniques
- Additional model / agent connectors
- Detection improvements
- Documentation and examples
- Testing and feedback

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This software is provided for defensive security research and authorized testing only.  
The authors and contributors assume no liability for misuse.  
Always obtain proper written authorization before testing any system.

---

**VeilForge** — Raising the security baseline for the next generation of intelligent systems.
