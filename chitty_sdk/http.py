"""HTTP helpers for Chitty Workspace marketplace packages.

Provides thin wrappers around :mod:`requests` (or :mod:`urllib.request` as a
zero-dependency fallback) so that tool scripts can make authenticated API
calls without boilerplate.

Install the ``http`` extra for the best experience::

    pip install chitty-sdk[http]
"""

from typing import Any, Dict, Optional


class ChittyApiError(Exception):
    """Raised when an API call returns a non-2xx status code.

    Attributes:
        status_code: HTTP status code.
        body: Response body as a string.
    """

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


# --------------------------------------------------------------------------- #
# Internal transport layer
# --------------------------------------------------------------------------- #

def _build_headers(token: Optional[str], extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers


def _requests_available() -> bool:
    try:
        import requests  # noqa: F401
        return True
    except ImportError:
        return False


def _do_request(
    method: str,
    url: str,
    token: Optional[str] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
    json_data: Any = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute an HTTP request and return parsed JSON.

    Uses :mod:`requests` when available, otherwise falls back to
    :mod:`urllib.request` so the SDK works without optional dependencies.
    """
    import json as _json

    hdrs = _build_headers(token, headers)

    if _requests_available():
        import requests as _req

        resp = _req.request(
            method,
            url,
            headers=hdrs,
            params=params,
            data=data,
            json=json_data if json_data is not None else None,
            timeout=30,
        )
        if not (200 <= resp.status_code < 300):
            raise ChittyApiError(resp.status_code, resp.text)
        if not resp.content:
            return {}
        return resp.json()  # type: ignore[no-any-return]

    # Fallback: urllib (no extra dependency)
    import urllib.request
    import urllib.error
    import urllib.parse

    if params:
        sep = "&" if "?" in url else "?"
        url = url + sep + urllib.parse.urlencode(params)

    body: Optional[bytes] = None
    if json_data is not None:
        body = _json.dumps(json_data).encode("utf-8")
    elif data is not None:
        body = data

    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            return _json.loads(raw)  # type: ignore[no-any-return]
    except urllib.error.HTTPError as exc:
        raise ChittyApiError(exc.code, exc.read().decode("utf-8", errors="replace")) from exc


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #

def api_get(
    url: str,
    token: Optional[str] = None,
    params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Send an HTTP GET request with optional Bearer authentication.

    Args:
        url: Fully-qualified URL.
        token: Bearer token.  Omit for unauthenticated requests.
        params: Query-string parameters.

    Returns:
        Parsed JSON response body.

    Raises:
        ChittyApiError: If the response status is not 2xx.
    """
    return _do_request("GET", url, token=token, params=params)


def api_post(
    url: str,
    token: Optional[str] = None,
    data: Optional[bytes] = None,
    json_data: Any = None,
) -> Dict[str, Any]:
    """Send an HTTP POST request with optional Bearer authentication.

    Args:
        url: Fully-qualified URL.
        token: Bearer token.
        data: Raw bytes body.  Mutually exclusive with *json_data*.
        json_data: Object to JSON-encode as the request body.

    Returns:
        Parsed JSON response body.

    Raises:
        ChittyApiError: If the response status is not 2xx.
    """
    return _do_request("POST", url, token=token, data=data, json_data=json_data)


def api_put(
    url: str,
    token: Optional[str] = None,
    json_data: Any = None,
) -> Dict[str, Any]:
    """Send an HTTP PUT request with optional Bearer authentication.

    Args:
        url: Fully-qualified URL.
        token: Bearer token.
        json_data: Object to JSON-encode as the request body.

    Returns:
        Parsed JSON response body.

    Raises:
        ChittyApiError: If the response status is not 2xx.
    """
    return _do_request("PUT", url, token=token, json_data=json_data)


def api_delete(
    url: str,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Send an HTTP DELETE request with optional Bearer authentication.

    Args:
        url: Fully-qualified URL.
        token: Bearer token.

    Returns:
        Parsed JSON response body.

    Raises:
        ChittyApiError: If the response status is not 2xx.
    """
    return _do_request("DELETE", url, token=token)
