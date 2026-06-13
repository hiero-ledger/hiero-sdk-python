from __future__ import annotations

from dataclasses import dataclass

from tck.util.key_utils import KeyType


@dataclass
class KeyGenerationParams:
    type: KeyType = None
    fromKey: str | None = None
    threshold: int | None = None
    keys: list[KeyGenerationParams] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> KeyGenerationParams:
        key_list = params.get("keys") or []

        raw_threshold = params.get("threshold")
        if raw_threshold is not None:
            # The dataclass field is declared `int | None` and the downstream
            # call site (`int(params.threshold)` in `_handle_key_list`) only
            # accepts integer-shaped values, but the previous parser passed
            # `params.get("threshold")` through unchecked, so a test (or a
            # typo in a TCK spec test) sending `threshold: "three"`, `3.5` as
            # a string, or `threshold: {}` would raise ValueError/TypeError
            # out of `int(...)` and bubble all the way up to a generic
            # internal_error instead of a descriptive invalid_params_error.
            # bool is technically an int subclass, but `threshold: true` is
            # semantically meaningless for a threshold count, so reject it
            # explicitly. Floats are rejected because they are almost always
            # a spec error (a threshold of 2.5 has no well-defined meaning).
            if isinstance(raw_threshold, bool) or not isinstance(
                raw_threshold, int
            ):
                raise ValueError(
                    f"threshold must be an integer, got {type(raw_threshold).__name__}: {raw_threshold!r}"
                )
            if raw_threshold < 0:
                raise ValueError(
                    f"threshold must be a non-negative integer, got {raw_threshold}"
                )

        return cls(
            type=(KeyType.from_string(params.get("type")) if params.get("type") else None),
            fromKey=params.get("fromKey"),
            threshold=raw_threshold,
            keys=[cls.parse_json_params(k) for k in key_list],
        )
