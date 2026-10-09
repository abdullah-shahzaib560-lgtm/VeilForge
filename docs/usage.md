# Usage Guide

## Installation

git clone https://github.com/abdullah-shahzaib560-lgtm/VeilForge.git
cd VeilForge
python -m venv .venv
source .venv/bin/activate
pip install -e .

## Basic Commands

veilforge --help
veilforge version
veilforge info

## Running Scans

veilforge scan llama3.2:1b --provider ollama
veilforge scan llama3.2:1b --provider ollama -v
veilforge scan llama3.2:1b --provider ollama --timeout 180
veilforge scan "I follow all rules" --provider dummy -v

## Reports

After every scan, reports are saved in the reports/ folder:
- JSON report
- HTML report (open in browser)

## Docker

docker compose build
docker compose run --rm veilforge scan llama3.2:1b --provider ollama
