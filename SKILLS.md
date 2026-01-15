---
description: Complete guide to using auto-bugherd for automated QA and BugHerd integration
---

# Auto-BugHerd QA Tool - Skills Guide

This guide contains everything you need to know to effectively use the `auto-bugherd` tool for automated website QA and BugHerd ticket management.

## Overview

`auto-bugherd` is a Python-based QA automation tool that:
- Verifies website content against Google Docs "Source of Truth"
- Checks SEO metadata (Title, Meta Description, H1)
- Validates metrics and copy accuracy
- Detects broken links
- Automatically creates BugHerd tickets with element selectors
- Supports webhook-based reactive QA

## Prerequisites

### Required
- Python 3.8+
- BugHerd API Key (set as `BUGHERD_API_KEY` environment variable)
- Dependencies: `requests`, `beautifulsoup4`, `flask` (for webhooks)

### Optional
- `BUGHERD_WEBHOOK_SECRET` for secure webhook listener
- Google Docs with published content (for source of truth comparison)

## Installation

```bash
# Clone the repository
git clone https://github.com/motacola/Auto-Bugherd.git
cd Auto-Bugherd

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BUGHERD_API_KEY="your_api_key_here"
export BUGHERD_WEBHOOK_SECRET="your_secret_here"  # Optional
```

## Core Usage Patterns

### 1. Ad-Hoc URL Check (Quick Validation)

Check a single URL without creating tickets:

```bash
python3 -m src.engine --url https://example.com
```

With Google Doc comparison:

```bash
python3 -m src.engine \
  --url https://example.com \
  --doc-url https://docs.google.com/document/d/YOUR_DOC_ID/pub
```

With link checking:

```bash
python3 -m src.engine \
  --url https://example.com \
  --check-links
```

### 2. Ad-Hoc with Auto-Ticketing

Create BugHerd tickets automatically for issues found:

```bash
python3 -m src.engine \
  --url https://example.com \
  --doc-url https://docs.google.com/document/d/YOUR_DOC_ID/pub \
  --ticket \
  --project-id 123456
```

**Important:** Tickets created this way include:
- CSS selectors for the problematic element
- XPath for precise location
- Context snippets for visual confirmation

### 3. Project-Based QA (Batch Mode)

Run QA across multiple pages defined in `config.json`:

```bash
python3 -m src.engine PROJECT_ID
```

With auto-ticketing:

```bash
python3 -m src.engine PROJECT_ID --ticket
```

With link checking:

```bash
python3 -m src.engine PROJECT_ID --check-links
```

## Configuration

### config.json Structure

```json
{
  "settings": {
    "user_agent": "Mozilla/5.0...",
    "timeout": 10
  },
  "projects": [
    {
      "id": "minuteman",
      "name": "Minuteman Plumbing",
      "bugherd_project_id": 489477,
      "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/pub",
      "live_pages": {
        "Water Heaters": "https://www.minutemanplumbing.com/plumbing/water-heaters",
        "Cambridge": "https://www.minutemanplumbing.com/locations/cambridge"
      },
      "rules": {
        "bad_phrases": [
          "Lorem ipsum",
          "Coming soon"
        ]
      }
    }
  ]
}
```

### Google Doc Format

For best results, structure your Google Doc with:

```
SEO Title: Your Page Title Here
Meta Description: Your meta description here
H1: Your main heading

Metrics That Matter:
- 25+ Years
- 4.9 Stars
- 50+ Service areas

[Rest of your content...]
```

## Advanced Features

### Webhook Listener (Reactive Mode)

Start the webhook listener to automatically run QA when BugHerd tasks are created:

```bash
python3 -m src.webhook_listener
```

Configure BugHerd webhook:
1. Go to BugHerd Project Settings → Integrations → Webhooks
2. Add webhook URL: `http://your-server:5000/webhook`
3. Add custom header: `X-BugHerd-Secret: your_secret_here`
4. Select events: `task_create`, `task_update`

### Element Selector Enrichment

When tickets are created with `--ticket`, they automatically include:

```
**SEO Title Mismatch**

Element: <title>
Expected: Best Plumbing in Cambridge
Found: Plumbing Services

📍 Element Location:
- CSS Selector: `title`
- XPath: `/html/head/title`
- Context: "Plumbing Services | Minuteman..."

🔗 Page URL: https://example.com
```

Developers can use the CSS selector in browser DevTools:
```javascript
document.querySelector('title')
```

### Link Checking

The link checker:
- Runs in parallel (10 concurrent requests by default)
- Ignores social media domains (Facebook, Twitter, LinkedIn, etc.) to avoid false positives
- Uses HEAD requests first, falls back to GET if blocked
- Reports 400+ status codes as broken

## HTML Reports

All QA runs generate HTML reports in the `reports/` directory:

```
reports/
├── report_ad-hoc_run_20260115_083000.html
├── report_minuteman_plumbing_20260115_090000.html
```

Reports include:
- Pass/Fail status for each page
- Detailed issue lists
- Clickable URLs
- Professional styling

## Common Workflows

### Workflow 1: Pre-Launch QA

```bash
# 1. Check all pages for a project
python3 -m src.engine minuteman --check-links

# 2. Review HTML report
open reports/report_minuteman_plumbing_*.html

# 3. Create tickets for issues
python3 -m src.engine minuteman --ticket --check-links
```

### Workflow 2: Content Update Verification

```bash
# 1. Update Google Doc with new content
# 2. Run ad-hoc check
python3 -m src.engine \
  --url https://example.com/updated-page \
  --doc-url https://docs.google.com/document/d/YOUR_DOC_ID/pub

# 3. If issues found, create ticket
python3 -m src.engine \
  --url https://example.com/updated-page \
  --doc-url https://docs.google.com/document/d/YOUR_DOC_ID/pub \
  --ticket \
  --project-id 123456
```

### Workflow 3: Continuous Monitoring

```bash
# 1. Start webhook listener
python3 -m src.webhook_listener

# 2. Configure BugHerd webhook
# 3. Create tasks in BugHerd - QA runs automatically
# 4. Review automated comments in BugHerd tickets
```

## Troubleshooting

### Issue: "BugHerd API Key missing"
**Solution:** Set the environment variable:
```bash
export BUGHERD_API_KEY="your_key_here"
```

### Issue: "Could not fetch Google Doc content"
**Solution:** Ensure the Google Doc is published:
1. File → Share → Publish to web
2. Use the `/pub` URL, not `/edit`

### Issue: "Webhook listener is UNSECURE"
**Solution:** Set the webhook secret:
```bash
export BUGHERD_WEBHOOK_SECRET="your_secret_here"
```

### Issue: False positives for social media links
**Solution:** Social links are automatically ignored. If you need to check them, modify `ignored_domains` in `src/link_checker.py`.

### Issue: Fuzzy matching too strict/loose
**Solution:** Adjust threshold in `doc_parser.py`:
```python
fuzzy_match(needle, haystack, threshold=0.8)  # Default
fuzzy_match(needle, haystack, threshold=0.6)  # More lenient
```

## Performance Tips

1. **Link Checking:** Adjust parallel workers in `link_checker.py`:
   ```python
   LinkChecker(user_agent=ua, timeout=5, max_workers=20)  # Faster
   ```

2. **Timeout:** Increase for slow sites in `config.json`:
   ```json
   {"settings": {"timeout": 20}}
   ```

3. **Batch Processing:** Use project mode instead of multiple ad-hoc calls

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Use webhook secrets** in production
3. **Validate webhook payloads** before processing
4. **Run webhook listener behind a reverse proxy** (nginx, Caddy)
5. **Use HTTPS** for webhook endpoints

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: QA Check
on: [push]
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run QA
        env:
          BUGHERD_API_KEY: ${{ secrets.BUGHERD_API_KEY }}
        run: |
          pip install -r requirements.txt
          python3 -m src.engine minuteman
```

## Key Learnings

1. **BugHerd API Limitations:** Visual element pinning is NOT available via API - we work around this with CSS selectors and XPath in ticket descriptions.

2. **Social Media Links:** Always cause false positives (403/400 errors) - ignore them by default.

3. **Google Docs:** Must be published (`/pub` URL) and use consistent formatting for SEO metadata extraction.

4. **Fuzzy Matching:** Essential for handling minor variations in copy (whitespace, punctuation).

5. **Parallel Processing:** Link checking is 10x faster with ThreadPoolExecutor.

6. **Logging:** Unified logging across all modules makes debugging much easier in production.

## Support & Contribution

- **Repository:** https://github.com/motacola/Auto-Bugherd
- **Issues:** Report bugs via GitHub Issues
- **Documentation:** See README.md for quick start guide

## Version History

- **v2.2** - Element selector enrichment
- **v2.1** - Hardening (parallel links, webhook security, unified logging)
- **v2.0** - SEO checks, fuzzy matching, HTML reports, webhooks
- **v1.0** - Initial release with basic QA and BugHerd integration
