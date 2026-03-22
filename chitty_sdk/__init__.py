"""Chitty SDK -- helpers for building Chitty Workspace marketplace packages.

Quick start::

    from chitty_sdk import tool_main, require_google_token, api_get

    @tool_main
    def main(args):
        token = require_google_token()
        data = api_get("https://example.com/api/items", token=token)
        return {"items": data}
"""

__version__ = "0.1.0"

# -- auth ------------------------------------------------------------------
from chitty_sdk.auth import (
    get_credential,
    require_credential,
    get_google_token,
    get_slack_token,
    require_google_token,
    require_slack_token,
)

# -- config ----------------------------------------------------------------
from chitty_sdk.config import (
    load_config,
    check_feature,
    require_feature,
    get_allowed_resources,
    check_resource,
    require_resource,
)

# -- tool ------------------------------------------------------------------
from chitty_sdk.tool import (
    read_input,
    success,
    error,
    tool_main,
)

# -- http ------------------------------------------------------------------
from chitty_sdk.http import (
    api_get,
    api_post,
    api_put,
    api_delete,
    ChittyApiError,
)

# -- connection ------------------------------------------------------------
from chitty_sdk.connection import (
    send_ready,
    send_heartbeat,
    send_event,
    send_log,
    send_error,
    read_platform_message,
)

__all__ = [
    # auth
    "get_credential",
    "require_credential",
    "get_google_token",
    "get_slack_token",
    "require_google_token",
    "require_slack_token",
    # config
    "load_config",
    "check_feature",
    "require_feature",
    "get_allowed_resources",
    "check_resource",
    "require_resource",
    # tool
    "read_input",
    "success",
    "error",
    "tool_main",
    # http
    "api_get",
    "api_post",
    "api_put",
    "api_delete",
    "ChittyApiError",
    # connection
    "send_ready",
    "send_heartbeat",
    "send_event",
    "send_log",
    "send_error",
    "read_platform_message",
]
