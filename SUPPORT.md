# Support Guide

## Scope

This guide covers install, licensing, validation failures, and refund/revocation handling for Local API Contract Tester.

## Fast Triage

1. Ask for version and license status:
   - `contract-tester --version`
   - `contract-tester --license-status --license-json`
2. Ask for command used and exact error output.
3. Confirm input files exist and are readable.

## Install and Run

If running from source:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m contract_tester.cli --version
```

If running binary:

```powershell
.\contract-tester.exe --version
```

## License Troubleshooting

Check current status:

```powershell
contract-tester --license-status --license-json
```

Common status codes:

- `missing_key`: no key found, demo mode is expected.
- `malformed`: key format is invalid.
- `bad_signature`: key was tampered or signed with wrong private key.
- `expired`: key is valid but past expiry date.
- `not_yet_valid`: key `nbf` date is in the future.
- `revoked`: key `jti` or fingerprint exists in revoked list.
- `invalid_public_key`: runtime verifier key misconfigured.

Key loading order:

1. `CONTRACT_TESTER_LICENSE`
2. `CONTRACT_TESTER_LICENSE_FILE`
3. `./license.key`
4. `~/.contract_tester/license.key`

## Validation Troubleshooting

If users report too many errors:

1. Suggest `--max-errors 20` for initial triage.
2. Suggest `--ignore-unknown` if traffic includes endpoints outside the spec.
3. Suggest `--report report.html` to share readable findings.

Common root causes:

- OpenAPI path mismatch (template vs literal).
- Wrong status code schema.
- Missing `required` fields.
- Wrong JSON types in request/response payloads.

## Refund and Revocation Workflow

When refunding or removing access:

1. Revoke with audit note:
   - `python scripts/revoke_and_note.py --jti <license_id> --reason refund`
2. If `jti` unavailable, revoke by token:
   - `python scripts/revoke_and_note.py --token "<token>" --reason chargeback`
3. Keep `revoked_licenses.txt` in private admin storage and back it up.

## Escalation Checklist

Escalate internally if any of the following occurs:

- Valid license unexpectedly reports `bad_signature`.
- `invalid_public_key` appears after a release.
- Binary crashes before argument parsing.
- Factory readiness check fails unexpectedly:
  - `python scripts/check_factory_readiness.py`

