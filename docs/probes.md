# Probes

Probes are individual attack tests in VeilForge.

## Current Probe Categories

### Prompt Injection
- Direct Injection
- Instruction Override
- Encoding Bypass
- Payload Split
- Unicode Obfuscation
- Multilingual Injection

### Jailbreak
- Role-play Jailbreak
- Refusal Suppression
- Hypothetical Jailbreak

### Data Extraction
- System Prompt Extraction

## How Probes Work

1. A probe contains one or more attack prompts
2. Each prompt is sent to the target through a connector
3. The response is analyzed by the detect() method
4. Result is marked as VULNERABLE, OK, or ERROR

## Adding a New Probe

1. Create a new class that inherits from Probe
2. Define name, category, severity, prompts
3. Implement the detect() method
4. Add the class to ALL_PROBES
