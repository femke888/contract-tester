import json
from typing import Dict, List, Optional, Tuple, Union

from jsonschema import Draft7Validator

from .openapi import resolve_operation, resolve_schema


def _openapi_schema_to_jsonschema(schema: Dict) -> Dict:
    if not isinstance(schema, dict):
        return {}

    schema = dict(schema)

    if schema.get("nullable") is True:
        schema.pop("nullable", None)
        return {"anyOf": [schema, {"type": "null"}]}

    if "properties" in schema and "type" not in schema:
        schema["type"] = "object"

    return schema


def _pick_json_schema_from_content(content: Dict) -> Optional[Dict]:
    if not isinstance(content, dict):
        return None

    app_json = content.get("application/json") or {}
    if isinstance(app_json, dict) and app_json.get("schema") is not None:
        return app_json.get("schema")

    for ctype, item in content.items():
        if not isinstance(ctype, str) or not isinstance(item, dict):
            continue
        ctype_l = ctype.lower()
        if "json" in ctype_l:
            schema = item.get("schema")
            if schema is not None:
                return schema
    return None


def _pick_response_schema(operation: Dict, status: int) -> Optional[Dict]:
    responses = operation.get("responses", {}) or {}
    status_key = str(status)
    response = responses.get(status_key)
    if not response:
        status_class = f"{str(status)[0]}XX" if status >= 100 else None
        if status_class:
            response = responses.get(status_class)
    if not response:
        response = responses.get("default")
    if not response:
        return None

    content = response.get("content", {}) or {}
    return _pick_json_schema_from_content(content)


def _merge_parameters(path_item: Optional[Dict], operation: Dict) -> List[Dict]:
    params: Dict[Tuple[str, str], Dict] = {}
    for source in (path_item, operation):
        if not isinstance(source, dict):
            continue
        for item in (source.get("parameters") or []):
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            loc = item.get("in")
            if not name or not loc:
                continue
            params[(name, loc)] = item
    return list(params.values())


def _coerce_value(
    value: Optional[Union[str, List[str]]], schema: object
) -> Union[str, int, float, bool, List[str], None]:
    if value is None or not isinstance(schema, dict):
        return value
    typ = schema.get("type")
    if typ == "array":
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v for v in value.split(",") if v != ""]
        return value
    if not isinstance(value, str):
        return value
    if typ == "integer":
        try:
            return int(value)
        except Exception:
            return value
    if typ == "number":
        try:
            return float(value)
        except Exception:
            return value
    if typ == "boolean":
        v = value.strip().lower()
        if v in {"true", "1", "yes"}:
            return True
        if v in {"false", "0", "no"}:
            return False
        return value
    return value


def _validate_param(
    spec: Dict,
    param: Dict,
    value: Optional[Union[str, List[str]]],
    cache_resolved: Dict[str, Dict],
    cache_validator: Dict[str, Draft7Validator],
) -> Optional[str]:
    schema = param.get("schema")
    if not isinstance(schema, dict):
        return None
    validator = _validator_for_schema(
        spec, schema, cache_resolved=cache_resolved, cache_validator=cache_validator
    )
    if validator is None:
        return None
    coerced = _coerce_value(value, validator.schema)
    try:
        validator.validate(coerced)
    except Exception as exc:
        name = param.get("name") or "param"
        loc = param.get("in") or "param"
        return f"Invalid {loc} parameter '{name}': {exc}"
    return None


def _default_hint(key: str) -> Optional[str]:
    if key.startswith("operation.missing"):
        return "Add the endpoint/method to the OpenAPI spec or filter this traffic."
    if key.startswith("request.param.missing"):
        return "Add the required parameter to the request or mark it optional in the spec."
    if key.startswith("request.param.invalid"):
        return "Ensure the parameter value matches the schema type/format."
    if key.startswith("request.body.missing"):
        return "Send a request body or mark it optional in the spec."
    if key.startswith("request.body.invalid_json"):
        return "Send valid JSON for this request or adjust the content type."
    if key.startswith("request.body.schema"):
        return "Update the request body to match the schema or adjust the schema."
    if key.startswith("request.body.schema_missing"):
        return "Add a requestBody schema for this operation."
    if key.startswith("response.schema_missing"):
        return "Add a response schema for this status code in the spec."
    if key.startswith("response.schema_mismatch"):
        return "Compare the response payload to the schema and fix fields/types."
    return None


def _resolve_schema_cached(
    spec: Dict, schema: Optional[Dict], cache: Dict[str, Dict]
) -> Optional[Dict]:
    if not isinstance(schema, dict):
        return schema
    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in cache:
            return cache[ref]
        resolved = resolve_schema(spec, schema)
        if isinstance(resolved, dict):
            cache[ref] = resolved
        return resolved
    return schema


def _validator_for_schema(
    spec: Dict,
    schema: Optional[Dict],
    cache_resolved: Optional[Dict[str, Dict]] = None,
    cache_validator: Optional[Dict[str, Draft7Validator]] = None,
) -> Optional[Draft7Validator]:
    if not isinstance(schema, dict):
        return None
    if cache_resolved is None:
        cache_resolved = {}
    if cache_validator is None:
        cache_validator = {}
    resolved = _resolve_schema_cached(spec, schema, cache_resolved)
    jsonschema = _openapi_schema_to_jsonschema(resolved or {})
    try:
        key = json.dumps(jsonschema, sort_keys=True, separators=(",", ":"))
    except Exception:
        key = repr(jsonschema)
    validator = cache_validator.get(key)
    if validator is None:
        validator = Draft7Validator(jsonschema)
        cache_validator[key] = validator
    return validator


def validate_traffic_against_spec(
    spec: Dict,
    traffic: List[Dict],
    max_errors: Optional[int] = None,
    ignore_unknown: bool = False,
) -> Dict:
    errors: List[str] = []
    grouped: Dict[str, List[str]] = {}
    error_details: List[Dict[str, str]] = []
    total = 0
    stopped_early = False
    schema_cache: Dict[str, Dict] = {}
    validator_cache: Dict[str, Draft7Validator] = {}

    def _add_error(key: str, message: str, hint: Optional[str] = None):
        errors.append(message)
        grouped.setdefault(key, []).append(message)
        hint = hint or _default_hint(key)
        detail = {"key": key, "message": message}
        if hint:
            detail["hint"] = hint
        error_details.append(detail)

    for entry in traffic:
        total += 1
        method = entry.get("method")
        path = entry.get("path")
        status = entry.get("status")
        response_json = entry.get("response_json")
        query = entry.get("query") or {}
        headers = entry.get("headers") or {}
        request_json = entry.get("request_json")
        request_text = entry.get("request_text")
        request_content_type = entry.get("request_content_type")

        if not isinstance(method, str) or not isinstance(path, str):
            _add_error(
                "operation.invalid_traffic_entry",
                f"Invalid traffic entry method/path: {method} {path}",
            )
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break
            continue

        if not isinstance(status, int):
            _add_error(
                f"response.invalid_status|{method}|{path}",
                f"Invalid status for {method} {path}: {status}",
            )
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break
            continue

        op, template, path_item, path_params = resolve_operation(spec, path, method)
        if not op:
            if not ignore_unknown:
                _add_error("operation.missing", f"No operation for {method} {path}")
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break
            continue

        group_path = template or path or ""
        params = _merge_parameters(path_item, op)
        for param in params:
            name = param.get("name")
            loc = param.get("in")
            required = bool(param.get("required"))
            if not name or not loc:
                continue
            value = None
            if loc == "path":
                value = path_params.get(name)
            elif loc == "query":
                value = query.get(name)
            elif loc == "header":
                value = headers.get(str(name).lower())
            else:
                continue

            if value is None:
                if required:
                    _add_error(
                        f"request.param.missing|{method}|{group_path}",
                        f"Missing {loc} parameter '{name}' for {method} {group_path}",
                    )
                continue

            err = _validate_param(spec, param, value, schema_cache, validator_cache)
            if err:
                _add_error(
                    f"request.param.invalid|{method}|{group_path}",
                    f"{err} for {method} {group_path}",
                )
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break
        if stopped_early:
            break

        request_body = op.get("requestBody")
        if isinstance(request_body, dict):
            required = bool(request_body.get("required"))
            content = request_body.get("content", {}) or {}
            schema = _pick_json_schema_from_content(content)
            is_json = False
            if request_content_type:
                is_json = "json" in str(request_content_type).lower()
            if request_json is not None:
                is_json = True

            if required and request_json is None and request_text is None:
                _add_error(
                    f"request.body.missing|{method}|{group_path}",
                    f"Missing request body for {method} {group_path}",
                )
            elif schema is not None and is_json:
                validator = _validator_for_schema(
                    spec, schema, cache_resolved=schema_cache, cache_validator=validator_cache
                )
                if request_json is None and request_text is not None:
                    _add_error(
                        f"request.body.invalid_json|{method}|{group_path}",
                        f"Invalid JSON request body for {method} {group_path}",
                    )
                else:
                    try:
                        if validator is not None:
                            validator.validate(request_json)
                    except Exception as exc:
                        _add_error(
                            f"request.body.schema|{method}|{group_path}",
                            f"Request body schema mismatch for {method} {group_path}: {exc}",
                        )
            elif request_json is not None and schema is None:
                _add_error(
                    f"request.body.schema_missing|{method}|{group_path}",
                    f"No request schema for {method} {group_path}",
                )
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break

        schema = _pick_response_schema(op, status)
        if not schema:
            if response_json is None and status in {204, 304}:
                continue
            _add_error(
                f"response.schema_missing|{method}|{group_path}|{status}",
                f"No response schema for {method} {group_path} {status}",
            )
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break
            continue

        validator = _validator_for_schema(
            spec, schema, cache_resolved=schema_cache, cache_validator=validator_cache
        )

        try:
            if validator is not None:
                validator.validate(response_json)
        except Exception as exc:
            _add_error(
                f"response.schema_mismatch|{method}|{group_path}|{status}",
                f"Schema mismatch for {method} {group_path} {status}: {exc}",
            )
            if max_errors and len(errors) >= max_errors:
                stopped_early = True
                break

    return {
        "total_checks": total,
        "error_count": len(errors),
        "errors": errors,
        "errors_grouped": grouped,
        "error_details": error_details,
        "stopped_early": stopped_early,
    }
