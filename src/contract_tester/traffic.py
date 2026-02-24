import base64
import json
import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse


def _load_json_file(path: Path):
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw)


def _normalize_headers(headers: Optional[Dict]) -> Dict:
    if not isinstance(headers, dict):
        return {}
    out: Dict[str, str] = {}
    for key, value in headers.items():
        if key is None:
            continue
        k = str(key).strip().lower()
        if not k:
            continue
        out[k] = str(value) if value is not None else ""
    return out


def _normalize_query(query: Optional[Dict]) -> Dict:
    if not isinstance(query, dict):
        return {}
    return query


def _normalize_entry(entry: Dict) -> Optional[Dict]:
    try:
        method = entry["method"].upper()
        path = _normalize_path(entry["path"])
        status = int(entry["status"])
        response_json = entry.get("response_json")
        query = _normalize_query(entry.get("query"))
        headers = _normalize_headers(entry.get("headers"))
        request_json = entry.get("request_json")
        request_text = entry.get("request_text")
        request_content_type = entry.get("request_content_type")
        if request_json is None and request_text and not request_content_type:
            sniffed = _sniff_json(request_text)
            if sniffed is not None:
                request_json = sniffed
        return {
            "method": method,
            "path": path,
            "status": status,
            "response_json": response_json,
            "query": query,
            "headers": headers,
            "request_json": request_json,
            "request_text": request_text,
            "request_content_type": request_content_type,
        }
    except Exception:
        return None


def _parse_har(path: Path) -> List[Dict]:
    data = _load_json_file(path)
    log = data.get("log", {})
    entries = log.get("entries", []) or []
    normalized: List[Dict] = []

    for entry in entries:
        req = entry.get("request", {}) or {}
        res = entry.get("response", {}) or {}
        method = (req.get("method") or "").upper()
        url = req.get("url") or ""
        req_path = _normalize_path(urlparse(url).path or "/")
        query = _parse_query(url)
        status = res.get("status")
        content = (res.get("content") or {})
        text = content.get("text")
        encoding = (content.get("encoding") or "").lower()
        mime = (content.get("mimeType") or "").lower()
        request_headers = _har_headers(req.get("headers"))
        request_content_type = request_headers.get("content-type")
        request_json, request_text = _parse_request_body(
            req.get("postData"), request_content_type
        )

        response_json = None
        if text and ("json" in mime):
            try:
                payload = text
                if encoding == "base64":
                    payload = base64.b64decode(text).decode("utf-8", errors="replace")
                response_json = json.loads(payload)
            except Exception:
                response_json = None

        if method and status is not None:
            normalized.append(
                {
                    "method": method,
                    "path": req_path,
                    "status": int(status),
                    "response_json": response_json,
                    "query": query,
                    "headers": request_headers,
                    "request_json": request_json,
                    "request_text": request_text,
                    "request_content_type": request_content_type,
                }
            )

    return normalized


def _parse_curl_log(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    blocks: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if line.strip().startswith("curl "):
            if current:
                blocks.append(current)
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        blocks.append(current)

    normalized: List[Dict] = []
    for block in blocks:
        cmd = block[0]
        body_lines = block[1:]

        method = "GET"
        url = None
        try:
            tokens = shlex.split(cmd)
            for i, tok in enumerate(tokens):
                if tok in {"-X", "--request"} and i + 1 < len(tokens):
                    method = tokens[i + 1].upper()
                if tok.startswith("http://") or tok.startswith("https://"):
                    url = tok
        except Exception:
            continue

        status = None
        status_idx = None
        for i, line in enumerate(body_lines):
            match = re.search(r"(HTTPSTATUS|STATUS):\s*(\d{3})", line)
            if match:
                status = int(match.group(2))
                status_idx = i

        if status is None or url is None:
            continue

        body = "\n".join(body_lines[:status_idx]).strip()
        body = _strip_http_headers(body)

        response_json = None
        if body:
            try:
                response_json = json.loads(body)
            except Exception:
                response_json = None

        parsed = urlparse(url)
        req_path = _normalize_path(parsed.path or "/")
        query = _parse_query(url)

        headers, request_content_type = _parse_curl_headers(tokens)
        request_json, request_text = _parse_request_payload(tokens, request_content_type)

        normalized.append(
            {
                "method": method,
                "path": req_path,
                "status": status,
                "response_json": response_json,
                "query": query,
                "headers": headers,
                "request_json": request_json,
                "request_text": request_text,
                "request_content_type": request_content_type,
            }
        )

    return normalized


def _strip_http_headers(text: str) -> str:
    if "\r\n\r\n" in text:
        return text.split("\r\n\r\n", 1)[1].strip()
    if "\n\n" in text:
        return text.split("\n\n", 1)[1].strip()
    return text


def load_traffic(path: Union[str, Path]) -> List[Dict]:
    p = Path(path)
    if p.suffix.lower() == ".har":
        return _parse_har(p)

    try:
        data = _load_json_file(p)
    except Exception:
        data = None

    if isinstance(data, list):
        normalized = []
        for entry in data:
            norm = _normalize_entry(entry)
            if norm:
                normalized.append(norm)
        return normalized

    curl_items = _parse_curl_log(p)
    if curl_items:
        return curl_items

    raise ValueError("Unsupported traffic format")


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    try:
        parsed = urlparse(path)
        if parsed.scheme and parsed.netloc:
            path = parsed.path
        else:
            path = parsed.path or path
    except Exception:
        pass

    if "?" in path or "#" in path:
        path = path.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def _parse_query(url: str) -> Dict:
    try:
        parsed = urlparse(url)
        raw = parse_qs(parsed.query or "", keep_blank_values=True)
        query: Dict[str, Union[str, List[str]]] = {}
        for key, values in raw.items():
            if not values:
                query[key] = ""
            elif len(values) == 1:
                query[key] = values[0]
            else:
                query[key] = values
        return query
    except Exception:
        return {}


def _har_headers(headers: Optional[List[Dict]]) -> Dict:
    if not isinstance(headers, list):
        return {}
    out: Dict[str, str] = {}
    for item in headers:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower()
        value = item.get("value")
        if name:
            out[name] = str(value) if value is not None else ""
    return out


def _parse_request_body(
    post_data: Optional[Dict], content_type: Optional[str]
) -> Tuple[Optional[Union[Dict, List]], Optional[str]]:
    if not isinstance(post_data, dict):
        return None, None
    text = post_data.get("text")
    if text is None:
        return None, None
    mime = (post_data.get("mimeType") or content_type or "").lower()
    if "json" in mime:
        try:
            return json.loads(text), text
        except Exception:
            return None, text
    if content_type is None:
        sniffed = _sniff_json(text)
        if sniffed is not None:
            return sniffed, text
    return None, text


def _parse_curl_headers(tokens: List[str]) -> Tuple[Dict, Optional[str]]:
    headers: Dict[str, str] = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in {"-H", "--header"} and i + 1 < len(tokens):
            raw = tokens[i + 1]
            if ":" in raw:
                name, value = raw.split(":", 1)
                name = name.strip().lower()
                if name:
                    headers[name] = value.strip()
            i += 2
            continue
        i += 1
    return headers, headers.get("content-type")


def _parse_curl_payload(tokens: List[str]) -> Optional[str]:
    data = None
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in {"-d", "--data", "--data-raw", "--data-binary"} and i + 1 < len(tokens):
            data = tokens[i + 1]
            i += 2
            continue
        i += 1
    return data


def _parse_request_payload(
    tokens: List[str], content_type: Optional[str]
) -> Tuple[Optional[Union[Dict, List]], Optional[str]]:
    data = _parse_curl_payload(tokens)
    if data is None:
        return None, None
    ctype = (content_type or "").lower()
    if "json" in ctype:
        try:
            return json.loads(data), data
        except Exception:
            return None, data
    if not content_type:
        sniffed = _sniff_json(data)
        if sniffed is not None:
            return sniffed, data
    return None, data


def _sniff_json(text: str) -> Optional[Union[Dict, List]]:
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    if not stripped:
        return None
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return None
    try:
        data = json.loads(stripped)
    except Exception:
        return None
    if isinstance(data, (dict, list)):
        return data
    return None
