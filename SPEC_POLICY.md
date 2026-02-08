# SDK Specification Policy

The protobuf files under `/proto` are the source of truth for
what the Hedera network accepts.

They define wire format, semantic meaning, and contractual
requirements — not SDK architecture.

When reviewing changes, ensure:

- Values sent to the network map correctly to protobuf definitions.
- Required fields are validated before proto construction.
- RFC2119 requirements (MUST, SHALL, REQUIRED) are enforced.
- Limits such as size bounds, ranges, and uniqueness are implemented where missing.
- Enum mappings are correct.
- Signing requirements implied by the spec are visible or documented.

Do NOT require SDK structure, naming, or class design to mirror protobuf.

If the SDK intentionally diverges from the spec behavior,
the pull request MUST clearly explain why the divergence is safe.
