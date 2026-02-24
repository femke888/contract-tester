import hashlib
import json
from typing import Dict, Optional

from .openapi import iter_operations


def _hash_schema(schema: Optional[Dict]) -> str:
    if schema is None:
        return ""
    data = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def diff_specs(old_spec: Dict, new_spec: Dict) -> Dict:
    old_ops = {(p, m): op for p, m, op in iter_operations(old_spec)}
    new_ops = {(p, m): op for p, m, op in iter_operations(new_spec)}

    breaking = []

    for key in old_ops:
        if key not in new_ops:
            breaking.append(f"Removed operation {key[1].upper()} {key[0]}")

    for key, old_op in old_ops.items():
        new_op = new_ops.get(key)
        if not new_op:
            continue

        old_responses = old_op.get("responses", {}) or {}
        new_responses = new_op.get("responses", {}) or {}

        for status in old_responses:
            if status not in new_responses:
                breaking.append(f"Removed response {key[1].upper()} {key[0]} {status}")
                continue

            old_schema = (old_responses.get(status, {}) or {}).get("content", {})
            new_schema = (new_responses.get(status, {}) or {}).get("content", {})

            old_json = (old_schema.get("application/json") or {}).get("schema")
            new_json = (new_schema.get("application/json") or {}).get("schema")

            if _hash_schema(old_json) != _hash_schema(new_json):
                breaking.append(
                    f"Schema changed {key[1].upper()} {key[0]} {status} (potential break)"
                )

    return {
        "breaking_changes": breaking,
    }
