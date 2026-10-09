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

- Prompt injection (direct & indirect)
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
- Docker & Docker Compose support
- Extensible probe system (easy to add new attacks)

---

## Quick Start

### 1. Install locally

```bash
git clone https://github.com/abdullah-shahzaib560-lgtm/VeilForge.git
cd VeilForge
python -m venv .venv
source .venv/bin/activate
pip install -e .
