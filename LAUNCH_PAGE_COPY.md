# Launch Page Copy

## Hero

**Catch API contract breaks before deploy.**

Local API Contract Tester validates OpenAPI/JSON Schema contracts against real traffic logs and finds breaking mismatches in minutes.

One-time price. No SaaS lock-in. Runs locally.

Primary CTA: **Buy Now**
Secondary CTA: **See Demo Report**

## Value Props

- Local-first CLI for individual developers
- Validate real traffic against spec, not just static linting
- Detect breaking schema changes between versions
- Generate readable HTML reports for fast triage
- Signed offline licensing with one-time purchase model

## Who It’s For

- Solo backend developers shipping APIs
- Freelancers maintaining multiple client APIs
- Indie SaaS builders with no platform engineering team

## Pain to Outcome

Before:

- You deploy with “valid” specs but production payloads still break clients.
- Contract tools are often overbuilt for teams and expensive per-seat.

After:

- You run one command before deploy and catch schema mismatches early.
- You keep a local, repeatable quality gate with clear reports.

## Core Use Cases

1. Validate production/staging traffic against OpenAPI:
   - `contract-tester validate --spec api.yaml --traffic traffic.har --report report.html`
2. Compare spec versions for potential breaks:
   - `contract-tester diff --old api_v1.yaml --new api_v2.yaml`
3. Triage quickly with grouped errors and fix hints.

## Pricing Block

**Early Adopter License (One-Time): $79**

Includes:

- Lifetime access to current major version
- Local usage for one individual developer
- Standard updates and bugfixes

Optional note:

- Introductory launch discount for first 20 customers.

## Trust and Risk Reversal

- Transparent local workflow
- SHA-256 release checksums provided
- License status diagnostics built in
- 14-day refund policy (if desired)

## FAQ

**Does it send my API data anywhere?**  
No. It runs locally unless you choose your own data workflow.

**Do I need CI to use it?**  
No. Start locally from CLI, add CI later if needed.

**Is this subscription software?**  
No. One-time payment model for individual license.

**What formats are supported?**  
OpenAPI JSON/YAML, HAR, normalized JSON traffic, and curl-log traffic.

## Footer CTA

Stop shipping blind API changes. Add a local contract gate before deploy.

**Buy Now**

