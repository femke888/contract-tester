from datetime import datetime
from html import escape
from typing import Dict, List


def build_html_report(result: Dict) -> str:
    total = result.get("total_checks", 0)
    errors: List[str] = result.get("errors", []) or []
    error_details: List[Dict] = result.get("error_details", []) or []
    error_count = result.get("error_count", len(errors))
    stopped_early = result.get("stopped_early", False)
    license_status = result.get("license_status", {}) or {}
    demo_mode = not license_status.get("valid", True)

    grouped = result.get("errors_grouped", {}) or {}
    group_rows = "\n".join(
        f"<li><strong>{escape(k)}</strong> ({len(v)})</li>" for k, v in grouped.items()
    ) or "<li>None</li>"
    if error_details:
        rows = "\n".join(
            f"<li>{escape(str(item.get('message', '')))}"
            + (
                f"<div class=\"hint\">Hint: {escape(str(item.get('hint', '')))}</div>"
                if item.get("hint")
                else ""
            )
            + "</li>"
            for item in error_details
        )
    else:
        rows = "\n".join(f"<li>{escape(e)}</li>" for e in errors)
    rows = rows or "<li>None</li>"

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Contract Tester Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1 {{ margin-bottom: 8px; }}
    .meta {{ margin-bottom: 16px; color: #555; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 12px; background: #eee; }}
    .err {{ color: #b00020; }}
    .hint {{ color: #555; font-size: 0.9em; margin-top: 4px; }}
    .banner {{ padding: 10px 12px; border-radius: 6px; background: #fff3cd; color: #6b4f00; margin: 12px 0; }}
    .promo {{ padding: 12px; border-radius: 6px; background: #eef6ff; color: #123a6b; margin: 12px 0; }}
    .promo strong {{ display: block; margin-bottom: 4px; }}
  </style>
</head>
<body>
  <h1>Contract Tester Report</h1>
  {('<div class="banner"><strong>Demo mode:</strong> report limited by license restrictions.</div>' if demo_mode else '')}
  {('<div class="promo"><strong>Upgrade to Pro</strong>Remove demo limits, unlock unlimited reports, and export full results.</div>' if demo_mode else '')}
  <div class="meta">
    <span class="pill">Generated: {escape(datetime.utcnow().isoformat())}Z</span>
  </div>
  <p><strong>Total checks:</strong> {total}</p>
  <p><strong>Errors:</strong> <span class="err">{error_count}</span></p>
  <p><strong>Stopped early:</strong> {str(stopped_early).lower()}</p>
  <h2>Error groups</h2>
  <ol>
    {group_rows}
  </ol>
  <h2>Errors</h2>
  <ol>
    {rows}
  </ol>
</body>
</html>
"""
