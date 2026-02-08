# Hedera protobufs
The authoritative repository of [protocol buffers](https://developers.google.com/protocol-buffers) 
used by the Hedera Hashgraph public network, especially to define its gRPC API. Other repositories 
are used to deploy language-specific libraries generated 
from the _*.proto_ files in the following repositories:
 - [Java](https://github.com/hashgraph/hedera-protobufs-java)
 - [Go](https://github.com/hashgraph/hedera-protobufs-go)
 - [JS & Typescript](https://github.com/hashgraph/protobuf.js)
 - [C++](https://github.com/hashgraph/hedera-protobufs-cpp)
 - [Swift](https://github.com/hashgraph/hedera-protobufs-swift)

## Overview of services

There are five primary service families, which inter-operate on entities 
controlled by one (or more) Ed25519 or ECDSA(secp256k1) keypairs:
1. The [cryptocurrency service](services/crypto_service.proto),
for cryptocurrency accounts with transfers denominated 
in [hbar (ℏ)](https://help.hedera.com/hc/en-us/articles/360000674317-What-are-the-official-HBAR-cryptocurrency-denominations-).
2. The [consensus service](services/consensus_service.proto), for
fast and unbiased ordering of opaque binary messages exchanged on 
arbitrary topics.
3. The [smart contract service](services/smart_contract_service.proto), for
execution of Solidity contract creations and calls; contract may both possess
ℏ themselves and exchange it with non-contract accounts.
4. The [file service](services/file_service.proto), for storage and 
retrieval of opaque binary data.
5. The [token service](services/token_service.proto), for token related operations such as create, update, mint, burn, transfer etc.

There are also four secondary service families:
1. The [network service](services/network_service.proto), for operations scoped
to the network or its constituent nodes rather user-controlled entities as above.
2. The [scheduling service](services/schedule_service.proto), for scheduling a transaction to 
be executed when the ledger has received enough prequisite signatures. 
3. The [freeze service](services/freeze_service.proto), for use by 
privileged accounts to suspend network operations during a maintenance window.
4. The [util service](services/util_service.proto), for utility operations on the network.

It is important to note that most network services are gated by fees which 
must be paid in ℏ from a cryptocurrency account. The payer authorizes a
fee by signing an appropriate transaction with a sufficient subset of the 
cryptographic key(s) associated to their account.

## Overview of state
State directory and its subdirectories contain the protobuf files that define the state of the network.
The state is divided into the following subdirectories, based on the service modules:
1. [Token](services/state/token) - The state of the Token service.
2. [Consensus](services/state/consensus) - The state of the Consensus service.

The state directory and its subdirectories  are in preview and are subject to change.

# For Developers

## Branching
This repository uses a simple branching model with only one distinguished branch;
`main` points to the latest protobufs intended for the next deployment to mainnet. 
Tags such as `v0.12.0` mark commits used for testnet and mainnet deploys.

## PBJ Package Support
Proto files in this repo are generated into two kinds of Java files, one using **protoc** and other using 
[PBJ](https://github.com/hashgraph/pbj) a custom java code generation library for Hedera. To support PBJ all proto files
need to have an option of the form:
```
// <<<pbj.java_package = "com.hedera.hapi.node.token">>> This comment is special code for setting PBJ Compiler java package
```
To specify the Java package for PBJ generated model objects. This option is ignored by **protoc**. PBJ ignores the default 
option `option java_package = "com.hederahashgraph.api.proto.java";` which is used by **protoc** to generate Java files.
