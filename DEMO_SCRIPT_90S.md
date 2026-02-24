# 60-90s Demo Script

## Goal

Show how Local API Contract Tester catches a real contract issue before deploy.

## Recording Setup

- Terminal visible
- Sample files ready:
  - `tests/fixtures/sample_spec.json`
  - `tests/fixtures/sample_traffic.json`

## Script

### 0:00 - 0:10 Problem framing

"API contracts break in production even when specs look fine. I’ll show a local check that catches this before deploy."

### 0:10 - 0:20 Show command

Run:

```powershell
python -m contract_tester.cli validate --spec tests/fixtures/sample_spec.json --traffic tests/fixtures/sample_traffic.json --report report.html
```

### 0:20 - 0:40 Show results

"It validated traffic against spec, found a schema mismatch, and grouped errors by endpoint/status."

Highlight:
- total checks
- error count
- top error group

### 0:40 - 0:55 Show report

"Now I open `report.html` for a clean shareable report with details and fix hints."

### 0:55 - 1:10 Show diff use case

Run:

```powershell
python -m contract_tester.cli diff --old tests/fixtures/sample_spec.json --new tests/fixtures/sample_spec.json
```

"You can also compare versions for breaking changes."

### 1:10 - 1:20 Close CTA

"If you ship APIs as a solo dev, this gives you a local quality gate in one command. One-time purchase, no SaaS lock-in."

