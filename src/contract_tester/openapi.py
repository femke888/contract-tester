import json
from pathlib import Path
from typing import Dict, Iterator, Tuple, Union, Optional

import yaml


def load_spec(path: Union[str, Path]) -> Dict:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("OpenAPI spec must be a JSON/YAML object")
    if "paths" not in data:
        raise ValueError("OpenAPI spec missing 'paths'")
    return data


def get_paths(spec: Dict) -> Dict:
    return spec.get("paths", {}) or {}


def get_operation(spec: Dict, path: str, method: str) -> Optional[Dict]:
    paths = get_paths(spec)
    norm_path = _normalize_path(path)
    ops = paths.get(norm_path, {}) or {}
    direct = ops.get(method.lower())
    if direct:
        return direct

    best_op = None
    best_score = -1
    req_parts = _split_path(norm_path)
    for template, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        score = _match_template_score(_normalize_path(template), req_parts)
        if score is None:
            continue
        op = methods.get(method.lower())
        if op and score > best_score:
            best_score = score
            best_op = op
    return best_op


def resolve_operation(
    spec: Dict, path: str, method: str
) -> Tuple[Optional[Dict], Optional[str], Optional[Dict], Dict]:
    paths = get_paths(spec)
    norm_path = _normalize_path(path)
    methods = paths.get(norm_path)
    if isinstance(methods, dict):
        direct = methods.get(method.lower())
        if direct:
            return direct, norm_path, methods, {}

    best_op = None
    best_template = None
    best_methods = None
    best_params: Dict[str, str] = {}
    best_score = -1
    req_parts = _split_path(norm_path)
    for template, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        score = _match_template_score(_normalize_path(template), req_parts)
        if score is None:
            continue
        op = methods.get(method.lower())
        if op and score > best_score:
            best_score = score
            best_op = op
            best_template = _normalize_path(template)
            best_methods = methods
            best_params = _extract_path_params(best_template, req_parts)
    return best_op, best_template, best_methods, best_params


def iter_operations(spec: Dict) -> Iterator[Tuple[str, str, Dict]]:
    for path, methods in get_paths(spec).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.startswith("x-"):
                continue
            if not isinstance(op, dict):
                continue
            yield path, method.lower(), op


def resolve_schema(
    spec: Dict, schema: Optional[Dict], max_depth: int = 20, _seen: Optional[set] = None
) -> Optional[Dict]:
    if not isinstance(schema, dict):
        return schema
    if "$ref" not in schema:
        return schema

    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema
    if not ref.startswith("#/"):
        return schema

    if _seen is None:
        _seen = set()
    if ref in _seen or max_depth <= 0:
        return schema
    _seen.add(ref)

    parts = [p for p in ref.lstrip("#/").split("/") if p]
    node = spec
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return schema
        node = node[part]

    if not isinstance(node, dict):
        return schema

    if "$ref" in node:
        return resolve_schema(spec, node, max_depth=max_depth - 1, _seen=_seen)
    return node


def _split_path(path: str) -> list:
    if not path:
        return [""]
    if path == "/":
        return [""]
    return [p for p in path.split("/") if p]


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    if "?" in path or "#" in path:
        path = path.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def _match_template_score(template: str, req_parts: list) -> Optional[int]:
    tmpl_parts = _split_path(template)
    if len(tmpl_parts) != len(req_parts):
        return None
    score = 0
    for t, r in zip(tmpl_parts, req_parts):
        if t.startswith("{") and t.endswith("}"):
            continue
        if t == r:
            score += 1
            continue
        return None
    return score


def _extract_path_params(template: str, req_parts: list) -> Dict[str, str]:
    params: Dict[str, str] = {}
    tmpl_parts = _split_path(template)
    if len(tmpl_parts) != len(req_parts):
        return params
    for t, r in zip(tmpl_parts, req_parts):
        if t.startswith("{") and t.endswith("}"):
            name = t[1:-1].strip()
            if name:
                params[name] = r
    return params
