# Email Templates

Replace placeholders before sending:
- `{{customer_name}}`
- `{{order_id}}`
- `{{license_token}}`
- `{{support_email}}`
- `{{product_link}}`

## 1) Purchase Confirmation

Subject: Your Local API Contract Tester purchase (`{{order_id}}`)

Hi `{{customer_name}}`,

Thanks for purchasing Local API Contract Tester.

Your order ID: `{{order_id}}`

Your license key will arrive in a separate email shortly.

Download: `{{product_link}}`

If you need help, reply to this email or contact `{{support_email}}`.

## 2) License Delivery

Subject: Your license key for Local API Contract Tester

Hi `{{customer_name}}`,

Here is your license key:

`{{license_token}}`

Setup options:

1. Set environment variable:
   - `CONTRACT_TESTER_LICENSE={{license_token}}`
2. Or save key in `license.key` in your working directory.

Verify:

```powershell
contract-tester --license-status --license-json
```

If you hit any issue, contact `{{support_email}}`.

## 3) Refund Processed

Subject: Refund completed (`{{order_id}}`)

Hi `{{customer_name}}`,

Your refund for order `{{order_id}}` has been processed.

Please note the associated license has been revoked as part of refund handling.

If this was unexpected, reply to this email and we will review immediately.

