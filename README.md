# Local API Contract Tester (MVP)

A local-first CLI that validates API contracts (OpenAPI/JSON Schema) against real traffic and sample cases.

Docs:

- Support operations: `SUPPORT.md`
- Launch page copy: `LAUNCH_PAGE_COPY.md`
- Refund policy: `REFUND_POLICY.md`
- License terms: `LICENSE_TERMS.md`
- Customer emails: `EMAIL_TEMPLATES.md`
- 60-90s demo script: `DEMO_SCRIPT_90S.md`

## Quick start

1) Create a venv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Run:

```powershell
python -m contract_tester.cli validate --spec api.yaml --traffic traffic.har
python -m contract_tester.cli diff --old api_v1.yaml --new api_v2.yaml
python -m contract_tester.cli --version
python -m contract_tester.cli validate --spec api.yaml --traffic traffic.har --report report.html
python -m contract_tester.cli validate --spec api.yaml --traffic traffic.har --report
```

## Sample fixtures

Use the bundled fixtures for a quick demo:

```powershell
python -m contract_tester.cli validate --spec tests/fixtures/sample_spec.json --traffic tests/fixtures/sample_traffic.json
```

## Tests

```powershell
python -m unittest
```

## Lint

```powershell
ruff check .
```

## Build (PyInstaller)

```powershell
pip install pyinstaller
.\scripts\build.ps1
```

Build uses `src/contract_tester/__init__.py` as the single version source and regenerates `version.txt` automatically.

## Release

Run full release checks and build:

```powershell
.\scripts\release.ps1
```

Optional version bump before checks/build:

```powershell
.\scripts\release.ps1 -Bump patch
.\scripts\release.ps1 -Bump minor
.\scripts\release.ps1 -Bump major
```

Release writes `dist/SHA256SUMS.txt` for artifact integrity verification.
Release also enforces factory readiness checks (gitignore hygiene and non-placeholder embedded public key).

## Supported inputs (MVP)

- OpenAPI v3 JSON/YAML (limited schema support)
- Traffic:
  - HAR (Chrome/Firefox export)
  - Normalized JSON list (see below)
  - Curl log format (see below)

### Normalized traffic JSON format

```json
[
  {
    "method": "GET",
    "path": "/users/123",
    "status": 200,
    "response_json": {"id": 123, "name": "Ada"}
  }
]
```

### Curl log format

Create logs with:

```bash
curl -s -X GET https://api.example.com/users/123 -H "Accept: application/json" -w "\nHTTPSTATUS:%{http_code}\n"
```

Then save output like:

```text
curl -s -X GET https://api.example.com/users/123 -H "Accept: application/json"
{"id": 123, "name": "Ada"}
HTTPSTATUS:200
```

## Notes
- Basic local `$ref` resolution is supported for `#/components/schemas/*`, including nested refs.
- Use `--max-errors` to stop early on huge logs.
- Templated paths like `/users/{id}` are supported for matching.
- Query strings and trailing slashes in traffic paths are normalized.
- Use `--ignore-unknown` to skip traffic entries that aren't in the spec.
- Use `--report` (defaults to `report.html`) to generate a simple HTML report.
- Request validation covers path/query/header params and JSON request bodies.
- Error output is grouped by type and endpoint for faster triage, and includes fix hints.

## Licensing and demo mode (MVP)

If no valid license is found, the CLI runs in demo mode:

- Validation is limited to 25 traffic entries.
- Specs are limited to 30 paths.

You can provide a license key in one of these ways:

- Set `CONTRACT_TESTER_LICENSE` to your key.
- Set `CONTRACT_TESTER_LICENSE_FILE` to a file path containing your key.
- Create `license.key` in the current directory.
- Create `~/.contract_tester/license.key`.
- Use `--license-status` to print license state; add `--license-json` for JSON output.

License format and verification:

- Keys use signed token format: `CT1.<payload_b64url>.<signature_b64url>`.
- Signature uses ECDSA P-256 with SHA-256 over `<payload_b64url>`.
- Payload requires `exp` (`YYYY-MM-DD`), and supports `sub`, `plan`, and optional `nbf`.
- Validation returns explicit status codes such as `ok`, `expired`, `not_yet_valid`, `bad_signature`, and `malformed`.

For issuing keys:

- Use `scripts/generate_license.py` with an EC private key.
- Runtime verifies with embedded public key, or override with `CONTRACT_TESTER_LICENSE_PUBLIC_KEY`.
- Generate keypair:
  - `python scripts/generate_license_keys.py --private-out keys/license_private.pem --public-out keys/license_public.pem`
  - Optional embedded key update: add `--update-license-module`

Revocation:

- Add revoked `jti` values or SHA-256 token fingerprints to `revoked_licenses.txt` (one per line).
- Default lookup paths: `./revoked_licenses.txt` and `~/.contract_tester/revoked_licenses.txt`.
- Override path with `CONTRACT_TESTER_REVOKED_FILE`.
- Admin helper:
  - Revoke by id: `python scripts/revoke_license.py --jti lic_123`
  - Revoke by token: `python scripts/revoke_license.py --token "<token>"`
  - Revoke from file: `python scripts/revoke_license.py --token-file license.key`
  - Revoke with audit note: `python scripts/revoke_and_note.py --jti lic_123 --reason refund`

