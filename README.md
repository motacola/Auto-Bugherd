# auto-bugherd

An extensible QA automation tool for cross-referencing live website content against Google Docs and automatically managing BugHerd tickets.

## Features
- **Modular Config:** Add new sites to `config.json` without touching code.
- **Dynamic Source of Truth:** Scrapes Google Docs (Public) to verify live site copy.
- **Ad-Hoc Testing:** Run checks against any URL on the fly using CLI flags.
- **BugHerd Integration:** Automated ticket creation via API for content discrepancies.

## Installation
```bash
pip install requests beautifulsoup4
```

## Usage

### 1. Ad-Hoc Check (Interactive)
Specify a URL and optionally a Google Doc to compare against.
```bash
python3 -m src.engine --url https://example.com --doc-url https://docs.google.com/document/d/DOC_ID/edit
```

### 2. Run Pre-configured Project
```bash
python3 -m src.engine kinty-jones
```

### 3. Automated Ticketing
Set your BugHerd API Key as an environment variable and use the `--ticket` flag.
```bash
export BUGHERD_API_KEY='your_api_key'
python3 -m src.engine kinty-jones --ticket
```

### 4. Webhook Listener (Reactive Mode)
Listen for real-time BugHerd events and trigger QA checks automatically.
```bash
# Install dependencies
pip install flask

# Start the listener
python3 -m src.webhook_listener
```
*Note: You must expose your local port (e.g., via `ngrok`) and register the URL in BugHerd > Settings > Integrations > Webhooks.*

## Project Structure
- `config.json`: Project and rule definitions.
- `src/engine.py`: Core execution logic.
- `src/doc_parser.py`: Google Doc extraction.
- `src/bugherd_client.py`: BugHerd API interaction.
- `src/webhook_listener.py`: Real-time event responder.
- `.agent/workflows/`: AI automation scripts.
