# Chitty SDK

The official Python SDK for building [Chitty Workspace](https://chitty.ai) marketplace packages.

Replaces the duplicate `auth.py` and `config.py` files that every package used to copy. One install, all the helpers you need.

## Installation

```bash
pip install chitty-sdk
```

For HTTP helpers (uses `requests` under the hood):

```bash
pip install chitty-sdk[http]
```

The HTTP module falls back to `urllib` automatically when `requests` is not installed, so the extra is optional.

## Quick Start

```python
#!/usr/bin/env python3
from chitty_sdk import tool_main, require_google_token, api_get

@tool_main
def main(args):
    token = require_google_token()
    messages = api_get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        token=token,
        params={"q": "in:inbox", "maxResults": "10"},
    )
    return {"emails": messages.get("messages", [])}
```

That is a complete, working tool script. The `@tool_main` decorator handles reading JSON from stdin, writing the response to stdout, and catching exceptions.

## Modules

### `chitty_sdk.auth` -- Credential Management

Credentials are resolved in order: environment variable `CHITTY_CRED_{KEY}`, then OS keyring.

```python
from chitty_sdk import get_credential, require_credential

# Returns None if not found
api_key = get_credential("my_service_api_key")

# Prints error JSON and exits if not found
api_key = require_credential("my_service_api_key")
```

Provider shortcuts:

```python
from chitty_sdk import get_google_token, require_google_token
from chitty_sdk import get_slack_token, require_slack_token

token = require_google_token()  # or exits with error
token = get_slack_token()       # or None
```

### `chitty_sdk.config` -- Package Configuration

Read feature flags and resource allow-lists from `CHITTY_PACKAGE_CONFIG`.

```python
from chitty_sdk import load_config, check_feature, require_feature
from chitty_sdk import get_allowed_resources, check_resource, require_resource

# Load raw config
config = load_config()

# Feature flags (default to True when not configured)
if check_feature("allow_send_message"):
    send_it()

# Exit with error if feature is disabled
require_feature("allow_delete")

# Resource allow-lists
buckets = get_allowed_resources("buckets")  # [] means all allowed

if check_resource("channels", "general"):
    post_to_channel()

# Exit with error if resource is not allowed
require_resource("channels", "secret-ops")
```

### `chitty_sdk.tool` -- Tool Execution

Standard stdin/stdout JSON protocol for tool scripts.

```python
from chitty_sdk import read_input, success, error

args = read_input()       # Parse JSON from stdin
success({"key": "val"})   # Print success JSON, exit(0)
error("Something broke")  # Print error JSON, exit(0)
```

The `@tool_main` decorator combines all three:

```python
from chitty_sdk import tool_main

@tool_main
def main(args):
    if not args.get("name"):
        return {"error": "name is required"}
    return {"greeting": f"Hello, {args['name']}!"}
```

Note: `error()` and `require_*` functions exit with code 0, not 1. Tool errors are data for the LLM, not process crashes.

### `chitty_sdk.http` -- HTTP Helpers

Authenticated API calls with automatic JSON parsing.

```python
from chitty_sdk import api_get, api_post, api_put, api_delete
from chitty_sdk.http import ChittyApiError

# GET with bearer auth and query params
data = api_get("https://api.example.com/items", token="...", params={"limit": "10"})

# POST with JSON body
result = api_post("https://api.example.com/items", token="...", json_data={"name": "New Item"})

# PUT
api_put("https://api.example.com/items/123", token="...", json_data={"name": "Updated"})

# DELETE
api_delete("https://api.example.com/items/123", token="...")

# Error handling
try:
    data = api_get("https://api.example.com/secret", token="bad-token")
except ChittyApiError as e:
    print(f"Status {e.status_code}: {e.body}")
```

### `chitty_sdk.connection` -- Persistent Connections

For scripts that maintain a long-running connection (e.g. Slack Socket Mode).

```python
from chitty_sdk import send_ready, send_heartbeat, send_event
from chitty_sdk import send_log, send_error, read_platform_message

# Notify the platform
send_ready("Connected to Slack workspace Acme Corp")

# Keep-alive
send_heartbeat()

# Deliver an event for agent processing
send_event("mention", {"user": "U123", "text": "hello", "channel": "C456"})

# Logging
send_log("Processing event", level="info")
send_error("Token expired", fatal=True)

# Read a platform message (non-blocking, 1s timeout)
msg = read_platform_message(timeout=1.0)
if msg and msg.get("type") == "shutdown":
    cleanup()
```

## Full Example: Slack Tool

```python
#!/usr/bin/env python3
from chitty_sdk import tool_main, require_slack_token, check_feature, check_resource, api_post, error

@tool_main
def main(args):
    token = require_slack_token()
    channel = args.get("channel", "").lstrip("#")
    text = args.get("text", "")

    if not channel or not text:
        error("Both 'channel' and 'text' are required.")

    if not check_feature("allow_send_message"):
        error("Sending messages is disabled in package configuration.")

    if not check_resource("channels", channel):
        error(f"Channel '{channel}' is not in the allowed channels list.")

    result = api_post(
        "https://slack.com/api/chat.postMessage",
        token=token,
        json_data={"channel": channel, "text": text},
    )

    if not result.get("ok"):
        error(result.get("error", "Unknown Slack API error"))

    return {"channel": result["channel"], "ts": result["ts"], "message": f"Sent to #{channel}"}
```

## Documentation

Full documentation at [chitty.ai/docs/sdk](https://chitty.ai/docs/sdk).

## License

MIT
