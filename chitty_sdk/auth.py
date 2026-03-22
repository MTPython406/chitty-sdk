"""Credential management for Chitty Workspace marketplace packages.

Credentials are resolved in order:
1. Environment variable ``CHITTY_CRED_{KEY}`` (set by the platform executor)
2. OS keyring under the ``chitty-workspace`` service name

This module is the single source of truth for credential access. Package
developers should never read the keyring directly.
"""

import json
import os
import sys
from typing import Optional


_KEYRING_SERVICE = "chitty-workspace"


def get_credential(key: str) -> Optional[str]:
    """Retrieve a credential by key.

    Checks the environment variable ``CHITTY_CRED_{KEY}`` first (upper-cased,
    hyphens replaced with underscores), then falls back to the OS keyring
    entry stored under the ``chitty-workspace`` service.

    Args:
        key: Credential identifier, e.g. ``"oauth_google_access_token"`` or
             ``"slack_app_token"``.

    Returns:
        The credential string, or ``None`` if not found.
    """
    env_key = f"CHITTY_CRED_{key.upper().replace('-', '_')}"
    value = os.environ.get(env_key)
    if value:
        return value

    try:
        import keyring
        value = keyring.get_password(_KEYRING_SERVICE, key)
        if value:
            return value
    except ImportError:
        pass
    except Exception:
        pass

    return None


def require_credential(key: str) -> str:
    """Retrieve a credential or terminate with an error payload.

    Behaves like :func:`get_credential` but prints an error JSON object to
    stdout and exits with code 0 when the credential is missing.  Exiting
    with 0 (not 1) is intentional -- tool errors are data, not crashes.

    Args:
        key: Credential identifier.

    Returns:
        The credential string.
    """
    value = get_credential(key)
    if value is not None:
        return value

    print(json.dumps({
        "success": False,
        "error": (
            f"Credential '{key}' not found. "
            f"Ensure the package is configured correctly, or set the "
            f"CHITTY_CRED_{key.upper().replace('-', '_')} environment variable."
        ),
    }))
    sys.exit(0)


# ---- Provider shortcuts -------------------------------------------------- #

def get_google_token() -> Optional[str]:
    """Shortcut for ``get_credential("oauth_google_access_token")``."""
    return get_credential("oauth_google_access_token")


def get_slack_token() -> Optional[str]:
    """Shortcut for ``get_credential("oauth_slack_access_token")``."""
    return get_credential("oauth_slack_access_token")


def require_google_token() -> str:
    """Shortcut for ``require_credential("oauth_google_access_token")``."""
    return require_credential("oauth_google_access_token")


def require_slack_token() -> str:
    """Shortcut for ``require_credential("oauth_slack_access_token")``."""
    return require_credential("oauth_slack_access_token")
