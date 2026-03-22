"""Connection script helpers for Chitty Workspace persistent connections.

Persistent connections (e.g. Slack Socket Mode) communicate with the platform
over a bi-directional NDJSON protocol on stdin/stdout.

**Outbound (stdout -> platform):**

* ``ready``     -- signal that the connection is established
* ``heartbeat`` -- keep-alive ping
* ``event``     -- deliver an incoming event to the agent
* ``log``       -- informational log line
* ``error``     -- report a problem (optionally fatal)

**Inbound (stdin <- platform):**

* ``response``      -- agent reply to a previously sent event
* ``shutdown``      -- graceful shutdown request
* ``config_update`` -- runtime configuration change

Stdout is forced to line-buffered mode on import so every
:func:`json.dumps` call produces exactly one NDJSON line.
"""

import json
import select
import sys
import uuid
from typing import Any, Dict, Optional


# Force line-buffered stdout for NDJSON protocol reliability.
try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except AttributeError:
    # Python builds where reconfigure is unavailable (very rare).
    pass


def _send(msg: Dict[str, Any]) -> None:
    """Write a single JSON line to stdout."""
    print(json.dumps(msg, ensure_ascii=False), flush=True)


# ---- Outbound messages --------------------------------------------------- #

def send_ready(message: str = "") -> None:
    """Notify the platform that the connection is established.

    Args:
        message: Human-readable status message (e.g. workspace name).
    """
    _send({"type": "ready", "message": message})


def send_heartbeat() -> None:
    """Send a keep-alive heartbeat to the platform."""
    _send({"type": "heartbeat"})


def send_event(
    event_id: str,
    data: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> None:
    """Deliver an incoming event to the platform for agent processing.

    Args:
        event_id: Short event type label (e.g. ``"mention"``, ``"dm"``).
        data: Arbitrary event payload.
        correlation_id: Unique ID to correlate the platform's response with
                        this event.  Auto-generated when omitted.
    """
    _send({
        "type": "event",
        "event_id": event_id,
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "data": data,
    })


def send_log(message: str, level: str = "info") -> None:
    """Send a log line to the platform.

    Args:
        message: Log text.
        level: Severity -- ``"debug"``, ``"info"``, ``"warn"``, or ``"error"``.
    """
    _send({"type": "log", "level": level, "message": message})


def send_error(message: str, fatal: bool = False) -> None:
    """Report an error to the platform.

    Args:
        message: Description of the error.
        fatal: If ``True``, the platform will treat this as an unrecoverable
               failure and tear down the connection.
    """
    _send({"type": "error", "message": message, "fatal": fatal})


# ---- Inbound messages ---------------------------------------------------- #

def read_platform_message(timeout: float = 1.0) -> Optional[Dict[str, Any]]:
    """Read one NDJSON message from stdin (non-blocking).

    Uses :func:`select.select` to avoid blocking forever.  On Windows,
    ``select`` only works on sockets, so the function falls back to a
    blocking read with a short timeout via a background thread.

    Args:
        timeout: Maximum seconds to wait for data.  Defaults to 1.0.

    Returns:
        Parsed message dict, or ``None`` if no message was available within
        the timeout or stdin is closed.
    """
    try:
        # Try select-based non-blocking read (works on Unix).
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if not ready:
            return None
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            return None
        return json.loads(line)
    except (ValueError, OSError):
        # select doesn't support pipes on Windows -- fall back to
        # a threaded approach.
        return _read_with_thread(timeout)
    except json.JSONDecodeError:
        return None


def _read_with_thread(timeout: float) -> Optional[Dict[str, Any]]:
    """Windows fallback: read stdin in a daemon thread with a timeout."""
    import threading

    result: Dict[str, Any] = {}
    error_flag: list = []

    def _reader() -> None:
        try:
            line = sys.stdin.readline()
            if line:
                result.update(json.loads(line.strip()))
        except Exception:
            error_flag.append(True)

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive() or error_flag or not result:
        return None
    return result
