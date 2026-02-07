# Worked Example: Hedera Protobuf Round Trip

This worked example demonstrates a complete protobuf request/response lifecycle
as used internally by the Hedera SDK.

The accompanying Python script (`examples/protobuf_round_trip.py`) is fully runnable and
contains no instructional narration — all explanation is contained here.

---

## Overview of the Flow

This example walks through the following steps:

1. Constructing a `CryptoGetInfoQuery` protobuf message
2. Wrapping it in a Hedera `Query` envelope using a `oneof`
3. Serializing the query into bytes
4. Deserializing the bytes back into a protobuf message
5. Mocking a Hedera `Response`
6. Serializing and deserializing the response
7. Extracting account data from the decoded response

This mirrors how the SDK constructs, sends, and interprets network messages.

---

## Step 1: Building the CryptoGetInfoQuery

A `CryptoGetInfoQuery` requires an `AccountID`, which itself is a protobuf
message. This reinforces an important concept: identifiers in Hedera are
structured types, not primitives.

The query message is populated and then embedded inside a `Query` envelope.

---

## Step 2: Query Envelope and `oneof`

Hedera uses a single top-level `Query` message that contains a `oneof`
representing all possible query types.

Setting `query.cryptoGetInfo` automatically selects the active query type
within the envelope.

---

## Step 3: Serialization

Before transmission, protobuf messages are serialized into a compact binary
format using `SerializeToString()`.

This binary payload is what would be sent over the network.

---

## Step 4: Deserialization

The serialized bytes are parsed back into a protobuf object using
`ParseFromString()`, reconstructing the full message tree.

---

## Step 5: Mocking a Network Response

To simulate a network round-trip, the example constructs a
`CryptoGetInfoResponse` inside a `Response` envelope.

Only a subset of fields are populated to demonstrate default handling.

---

## Step 6: Interpreting the Response

Finally, the decoded response is traversed and relevant account information
is extracted, similar to how the SDK converts protobuf responses into
higher-level objects.

---

## Why This Example Matters

Understanding this flow allows SDK developers to:

- Debug protobuf serialization issues
- Reason about `oneof` selection
- Inspect raw network payloads
- Understand SDK abstraction boundaries

The full runnable implementation can be found in `protobuf_round_trip.py`.
