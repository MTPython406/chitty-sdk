"""Package configuration helpers for Chitty Workspace marketplace packages.

The platform injects a JSON blob via the ``CHITTY_PACKAGE_CONFIG`` environment
variable.  It contains two sections:

* **features** -- boolean flags that toggle capabilities on or off.
* **resources** -- allow-lists for scoped resources (channels, buckets, ...).

When no configuration is present, all features default to *enabled* and all
resources default to *allowed* (open access).
"""

import json
import os
import sys
from typing import Any, Dict, List


def load_config() -> Dict[str, Any]:
    """Load the package configuration from the environment.

    Returns:
        Parsed configuration dict.  Always contains at least ``features``
        and ``resources`` keys (both may be empty dicts).
    """
    raw = os.environ.get("CHITTY_PACKAGE_CONFIG", "")
    if not raw:
        return {"features": {}, "resources": {}}
    try:
        config = json.loads(raw)
    except json.JSONDecodeError:
        return {"features": {}, "resources": {}}
    config.setdefault("features", {})
    config.setdefault("resources", {})
    return config


# ---- Feature flags ------------------------------------------------------- #

def check_feature(feature_id: str, default: bool = True) -> bool:
    """Check whether a feature flag is enabled.

    Args:
        feature_id: Identifier of the feature (e.g. ``"allow_send_message"``).
        default: Value to return when the flag is not present in the
                 configuration.  Defaults to ``True`` (permissive).

    Returns:
        ``True`` if the feature is enabled, ``False`` otherwise.
    """
    config = load_config()
    return bool(config["features"].get(feature_id, default))


def require_feature(feature_id: str) -> None:
    """Assert that a feature flag is enabled, or exit with error JSON.

    Args:
        feature_id: Identifier of the feature.
    """
    if check_feature(feature_id):
        return
    print(json.dumps({
        "success": False,
        "error": (
            f"Feature '{feature_id}' is disabled in the package configuration. "
            f"Enable it in Settings > Marketplace > Package > Feature Flags."
        ),
    }))
    sys.exit(0)


# ---- Resource allow-lists ------------------------------------------------ #

def get_allowed_resources(resource_type: str) -> List[str]:
    """Return the allow-list for a resource type.

    Resource entries in the config may be plain strings or dicts with an
    ``id`` field.  Both forms are normalised to a flat list of strings.

    Args:
        resource_type: Kind of resource (e.g. ``"channels"``, ``"buckets"``).

    Returns:
        List of allowed resource identifiers.  An empty list means
        *no restrictions* (all resources allowed).
    """
    config = load_config()
    entries = config["resources"].get(resource_type, [])
    result: List[str] = []
    for entry in entries:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict) and "id" in entry:
            result.append(entry["id"])
    return result


def check_resource(resource_type: str, resource_id: str) -> bool:
    """Check whether a specific resource is in the allow-list.

    An empty allow-list means no restrictions -- all resources are allowed.

    Args:
        resource_type: Kind of resource.
        resource_id: Identifier of the resource to check.

    Returns:
        ``True`` if the resource is allowed.
    """
    allowed = get_allowed_resources(resource_type)
    if not allowed:
        return True
    return resource_id in allowed


def require_resource(resource_type: str, resource_id: str) -> None:
    """Assert that a resource is allowed, or exit with error JSON.

    Args:
        resource_type: Kind of resource.
        resource_id: Identifier of the resource to check.
    """
    if check_resource(resource_type, resource_id):
        return
    allowed = get_allowed_resources(resource_type)
    print(json.dumps({
        "success": False,
        "error": (
            f"Resource '{resource_id}' is not in the allowed {resource_type}. "
            f"Allowed: {', '.join(allowed)}. "
            f"Configure allowed {resource_type} in Settings > Marketplace > Package."
        ),
    }))
    sys.exit(0)
