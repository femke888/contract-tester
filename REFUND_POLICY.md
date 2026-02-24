# Refund Policy

## Local API Contract Tester Refund Policy

Effective date: 2026-02-17

## Eligibility

- Refund requests are accepted within 14 calendar days of purchase.
- Requests must come from the original purchaser email or include order reference.
- If a license has already been revoked due to abuse, refund may be denied.

## What qualifies

- Product fails to run on supported environment after reasonable troubleshooting.
- Key advertised feature is not available in shipped product.
- Duplicate purchase by mistake.

## What does not qualify

- Change of mind after significant usage and no technical issue.
- Feature requests for capabilities not advertised at time of purchase.
- Inability to use due to unsupported OS/runtime not listed as supported.

## Process

1. Send request with order ID and brief issue summary.
2. Support attempts one troubleshooting cycle.
3. If approved, refund is issued through payment provider.
4. License is revoked after refund confirmation.

## Revocation after refund

After approved refund, license access is removed:

```powershell
python scripts/revoke_and_note.py --jti <license_id> --reason refund
```

## Contact

Support channel: (set your email or helpdesk link here)

