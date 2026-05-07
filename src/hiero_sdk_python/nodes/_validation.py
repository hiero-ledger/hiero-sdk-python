"""Shared validation utilities for node transactions."""

from __future__ import annotations


def validate_associated_registered_nodes(ids: list[int]) -> None:
    """Validate a list of associated registered node IDs.

    Args:
        ids: List of registered node IDs to validate.

    Raises:
        ValueError: If any ID is invalid or the list exceeds 20 entries.
    """
    if len(ids) > 20:
        raise ValueError("associated_registered_nodes must have at most 20 entries")
    for node_id in ids:
        if not isinstance(node_id, int) or isinstance(node_id, bool) or node_id <= 0:
            raise ValueError("Each associated registered node ID must be a positive integer")
