# Protobuf Training for SDK Developers

This training is a **linear, explanatory course** designed for SDK developers who may have **little or no prior experience with Protocol Buffers (protobufs)**.

Its purpose is to explain *what protobufs are*, *why they exist*, and *how they are used in practice* inside the Hedera / Hiero SDK ecosystem. By the end of the course, you should not only be able to follow protobuf-based code, but also reason about it, debug it, and confidently work with it directly when necessary.

The course progresses from general concepts to Hedera‑specific details, and finishes with a complete, end‑to‑end worked example that mirrors how the SDK interacts with the Hedera network internally.

---

## Module 01: Google Protocol Buffers Fundamentals

Before working with Hedera, it is important to understand protobufs on their own.

Protocol Buffers are a **language-agnostic, strongly-typed, binary data format** created by Google. They are designed to solve problems that arise when systems need to exchange structured data reliably, efficiently, and in a way that can evolve over time without breaking compatibility.

In practice, protobufs replace formats like JSON or XML in systems where performance, strict schemas, and backward compatibility matter.

**Topics covered (with explanation):**

* **What Protocol Buffers are and why they are used**
  Protobufs define *what data is allowed* and *what shape it must have*. Unlike JSON, protobufs enforce structure at compile time and serialize into a compact binary form, making them faster and safer for network communication.

* **`.proto` files and schema definitions**
  A `.proto` file is the authoritative contract between systems. It defines messages, fields, and types. All generated code in every language comes from these files.

* **`message` definitions and field numbering**
  Messages describe structured data. Field numbers are not arbitrary — they are part of the binary encoding and must remain stable to preserve compatibility across versions.

* **Scalar types vs message types**
  Scalar fields represent primitive values (numbers, strings, booleans), while message fields allow nesting and composition of complex data structures.

* **`oneof` fields**
  A `oneof` enforces that only one field in a group may be set at a time. This is commonly used to model mutually exclusive options, such as different query or response types.

* **Binary serialization concepts**
  Protobufs encode data into bytes using field numbers and wire types. You do not need to know the wire format, but understanding that serialization is deterministic and compact helps with debugging.

**Goal:**
Build a strong conceptual understanding of protobufs as structured, version-safe data contracts.

---

## Module 02: Hedera Protobuf Architecture

Hedera exposes its entire public API using protobuf definitions. Every interaction with the network — queries, transactions, and responses — is described by protobuf messages.

This module explains how those messages are organized and why Hedera uses a layered envelope approach.

**Topics covered (with explanation):**

* **Hedera service definitions**
  Services group related functionality (for example, crypto, consensus, token). Each service defines the protobuf messages used for its operations.

* **Query and Response envelope pattern**
  Rather than sending many different top-level message types, Hedera wraps all queries in a `Query` message and all replies in a `Response` message.

* **Use of `oneof` for query and response selection**
  The envelope uses `oneof` fields to indicate *which specific operation* is being requested or returned.

* **Request / response pairing**
  Every query message has a corresponding response message, and understanding this pairing is essential when navigating protobuf definitions.

* **Headers and precheck status codes**
  Response headers contain metadata about execution status before any business logic runs. These are critical when debugging failed requests.

**Goal:**
Understand the structure of Hedera’s protobuf-based network API and how requests and responses are routed.

---

## Module 03: Python Generated Protobuf Classes

Protobuf schemas are not used directly at runtime. Instead, they are compiled into language-specific classes that enforce the schema rules.

This module focuses on how `.proto` definitions become **Python objects** and how those objects behave in real code.

**Topics covered (with explanation):**

* **Generated `*_pb2.py` files**
  These files contain Python classes that mirror the message definitions in `.proto` files. They should not be edited manually.

* **Message instantiation and default values**
  Creating a protobuf object does not mean fields are "set". Unset fields have implicit defaults, which can affect logic if misunderstood.

* **Nested messages**
  Some fields are themselves messages. Understanding how to access and populate nested messages is critical for correct request construction.

* **`CopyFrom` vs direct assignment**
  Certain message fields must be populated using `CopyFrom` to preserve type safety and internal consistency.

* **Inspecting and printing protobuf messages**
  Protobuf objects can be printed for debugging, but the output reflects structure, not wire format.

**Goal:**
Gain confidence working directly with Python-generated protobuf classes without relying on SDK abstractions.

---

## Module 04: Converting Data *To* Protobuf Messages

Before data can be sent to the Hedera network, it must be translated into a protobuf message that exactly matches the expected schema.

This module explains how application-level data becomes a valid protobuf request.

**Topics covered (with explanation):**

* **Manually constructing protobuf messages**
  Understanding how to create messages step by step helps when debugging SDK behavior or writing low-level tooling.

* **Populating nested message fields**
  Many Hedera messages contain nested structures that must be explicitly populated.

* **Working with IDs and basic types**
  Identifiers such as `AccountID` are protobuf messages themselves, not simple integers.

* **Validating message completeness**
  While protobufs allow unset fields, the network may reject incomplete or malformed requests.

**Goal:**
Understand how raw input data is translated into a network-ready protobuf message.

---

## Module 05: Converting Data *From* Protobuf Messages

When the network responds, it returns structured protobuf messages that must be interpreted correctly.

This module explains how to safely extract and reason about response data.

**Topics covered (with explanation):**

* **Navigating nested protobuf structures**
  Responses often contain deeply nested messages that must be accessed carefully.

* **Reading scalar and message fields**
  Understanding when a field is present versus when it is simply defaulted is critical.

* **Unset fields and defaults**
  Protobufs do not distinguish between "unset" and "set to default" in all cases, which can be surprising.

* **Mapping protobufs to SDK objects**
  SDKs typically convert protobuf responses into higher-level objects. Understanding this mapping aids debugging.

**Goal:**
Correctly interpret network responses without misreading protobuf defaults or structure.

---

## Module 06: Serializing Protobuf Messages

Protobuf messages must be converted into bytes before they can be transmitted over the network.

This module explains what serialization does and where it fits in the request lifecycle.

**Topics covered (with explanation):**

* **`SerializeToString()`**
  This method converts a structured protobuf object into its binary wire representation.

* **Binary encoding characteristics**
  Serialized protobufs are compact and not human-readable, which is why logging must occur before serialization.

* **Payload size considerations**
  Field numbers, optional fields, and nesting all affect message size.

* **Serialization in the SDK**
  The SDK serializes messages immediately before network transmission.

* **Common serialization mistakes**
  Serializing incomplete messages or modifying messages after serialization can cause subtle bugs.

**Goal:**
Understand how and when protobuf messages become raw network bytes.

---

## Module 07: Deserializing Protobuf Messages

Deserialization is the process of reconstructing structured protobuf objects from raw bytes received from the network.

This module explains how incoming data becomes usable again.

**Topics covered (with explanation):**

* **`ParseFromString()`**
  This method populates a protobuf object from binary data.

* **Reconstructing message trees**
  Nested structures are rebuilt automatically based on the schema.

* **Error handling during parsing**
  Corrupt or unexpected data can cause parsing failures.

* **Validation after deserialization**
  Even successfully parsed messages should be checked for expected content.

**Goal:**
Safely reconstruct and validate protobuf messages received from the network.

---

## Module 08: Worked Example (End‑to‑End)

The final module brings together everything learned in the previous modules.

Rather than introducing new concepts, it demonstrates how all of the pieces work together in a realistic scenario.

**What the example demonstrates:**

* Manually constructing a Hedera query protobuf
* Wrapping the query in a Hedera `Query` envelope
* Serializing the query into bytes
* Mocking a Hedera network response
* Serializing and deserializing the response
* Extracting SDK‑level data from the decoded protobuf

**Goal:**
See how protobufs function across the full lifecycle of a Hedera SDK request.

**Resources:**
[Worked Example Documentation](ProtoBuf_Example.md)
[Runnable Python Script](../../../../examples/protobuf_round_trip.py)

---

## Next Steps

After completing this training, developers should be able to:

* Understand what protobufs are and why Hedera uses them
* Debug protobuf‑related SDK issues with confidence
* Manually construct and inspect Hedera protobuf messages
* Understand how SDK abstractions map to raw protobuf data
* Reason clearly about serialization and deserialization boundaries
