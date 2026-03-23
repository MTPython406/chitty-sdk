"""Tool execution helpers for Chitty Workspace marketplace packages.

Marketplace tool scripts communicate with the platform over stdin/stdout JSON.
This module standardises the boilerplate so every tool reads input and writes
output in exactly the same way.
"""

import functools
import io
import json
import os
import sys
import traceback
from typing import Any, Callable, Dict

# Force UTF-8 on Windows (default cp1252 can't handle emoji/unicode in tool output)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
# Also set env for child processes
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def read_input() -> Dict[str, Any]:
    """Read the tool arguments from stdin as JSON.

    Returns:
        Parsed argument dictionary.  Returns an empty dict if stdin is empty
        or contains invalid JSON.
    """
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def success(data: Any) -> None:
    """Print a success payload and exit.

    The platform expects ``{"success": true, "output": ...}`` on stdout.

    Args:
        data: Arbitrary JSON-serialisable value to return as the tool output.
    """
    print(json.dumps({"success": True, "output": data}, ensure_ascii=False))
    sys.exit(0)


def error(message: str) -> None:
    """Print an error payload and exit.

    Exits with code **0** -- tool errors are data, not process crashes.
    An exit code of 1 would cause the platform to treat the tool as broken
    rather than reporting the error to the LLM.

    Args:
        message: Human-readable error description.
    """
    print(json.dumps({"success": False, "error": message}, ensure_ascii=False))
    sys.exit(0)


def tool_main(fn: Callable[[Dict[str, Any]], Any]) -> Callable[[], None]:
    """Decorator that turns a plain function into a tool entry point.

    The decorated function:

    1. Reads JSON arguments from stdin.
    2. Calls *fn(args)* with the parsed dict.
    3. Wraps the return value in a success payload.
    4. Catches any exception and emits an error payload instead.

    Example::

        from chitty_sdk import tool_main

        @tool_main
        def main(args):
            name = args.get("name", "world")
            return {"greeting": f"Hello, {name}!"}

    The decorated function is immediately invoked when the module is loaded
    via ``if __name__ == "__main__"``, but you can also call it directly.
    """

    @functools.wraps(fn)
    def wrapper() -> None:
        try:
            args = read_input()
            result = fn(args)
            if result is not None:
                success(result)
        except SystemExit:
            raise
        except Exception as exc:
            tb = traceback.format_exc()
            error(f"{exc}\n\n{tb}")

    # Auto-invoke when the decorated module is executed as a script.
    # This lets developers write:
    #     @tool_main
    #     def main(args): ...
    # without needing a separate ``if __name__ == "__main__"`` block, but it
    # only fires when the *defining module* is the main script.
    import inspect
    caller_globals = inspect.stack()[1].frame.f_globals
    if caller_globals.get("__name__") == "__main__":
        wrapper()

    return wrapper
