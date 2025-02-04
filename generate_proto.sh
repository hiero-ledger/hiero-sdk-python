#!/bin/bash
set -e

hapi_version="v0.57.3"
protos_dir=".protos"
services_dir="src/hiero_sdk_python/hapi/services"
mirror_dir="src/hiero_sdk_python/hapi/mirror"

echo "Setting up directories..."
mkdir -p "$protos_dir"
rm -rf "$protos_dir"/*
rm -rf "$services_dir"/*
rm -rf "$mirror_dir"/*
mkdir -p "$services_dir/auxiliary/tss"
mkdir -p "$services_dir/event"
mkdir -p "$mirror_dir"
touch "$services_dir/__init__.py"
touch "$mirror_dir/__init__.py"

echo "Downloading Hedera protobufs version $hapi_version..."
curl -sL "https://github.com/hashgraph/hedera-protobufs/archive/refs/tags/${hapi_version}.tar.gz" \
  | tar -xz -C "$protos_dir" --strip-components=1

find "$protos_dir" -mindepth 1 -maxdepth 1 \
  ! -name platform ! -name services ! -name mirror -exec rm -r {} +

echo "Compiling service and platform protobuf files..."
python -m grpc_tools.protoc \
    --proto_path="$protos_dir/platform" \
    --proto_path="$protos_dir/services" \
    --pyi_out="./$services_dir" \
    --python_out="./$services_dir" \
    --grpc_python_out="./$services_dir" \
    "$protos_dir/services/"*.proto \
    "$protos_dir/services/auxiliary/tss/"*.proto \
    "$protos_dir/platform/event/"*.proto

echo "Adjusting imports for service and platform protobuf files..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    find "$services_dir" -type f -name "*.py" -exec sed -i '' \
        -e '/^import .*_pb2 as .*__pb2/s/^/from . /' \
        -e 's/^from auxiliary\.tss/from .auxiliary.tss/' \
        -e 's/^from event/from .event/' {} +
else
    find "$services_dir" -type f -name "*.py" -exec sed -i \
        -e '/^import .*_pb2 as .*__pb2/s/^/from . /' \
        -e 's/^from auxiliary\.tss/from .auxiliary.tss/' \
        -e 's/^from event/from .event/' {} +
fi

echo "Compiling mirror protobuf files..."
python -m grpc_tools.protoc \
    --proto_path="$protos_dir/mirror" \
    --proto_path="$protos_dir/services" \
    --python_out="$mirror_dir" \
    --grpc_python_out="$mirror_dir" \
    "$protos_dir/mirror/"*.proto

echo "Adjusting imports for mirror protobuf files..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    find "$mirror_dir" -type f -name "*.py" -exec sed -i '' \
        -e 's/^import basic_types_pb2 as/import hiero_sdk_python.hapi.services.basic_types_pb2 as/' \
        -e 's/^import timestamp_pb2 as/import hiero_sdk_python.hapi.services.timestamp_pb2 as/' \
        -e 's/^import consensus_submit_message_pb2 as/import hiero_sdk_python.hapi.services.consensus_submit_message_pb2 as/' \
        -e 's/^import consensus_service_pb2 as/import hiero_sdk_python.hapi.mirror.consensus_service_pb2 as/' \
        -e 's/^import mirror_network_service_pb2 as/import hiero_sdk_python.hapi.mirror.mirror_network_service_pb2 as/' {} +
else
    find "$mirror_dir" -type f -name "*.py" -exec sed -i \
        -e 's/^import basic_types_pb2 as/import hiero_sdk_python.hapi.services.basic_types_pb2 as/' \
        -e 's/^import timestamp_pb2 as/import hiero_sdk_python.hapi.services.timestamp_pb2 as/' \
        -e 's/^import consensus_submit_message_pb2 as/import hiero_sdk_python.hapi.services.consensus_submit_message_pb2 as/' \
        -e 's/^import consensus_service_pb2 as/import hiero_sdk_python.hapi.mirror.consensus_service_pb2 as/' \
        -e 's/^import mirror_network_service_pb2 as/import hiero_sdk_python.hapi.mirror.mirror_network_service_pb2 as/' {} +
fi

if [ "$(ls -A "$services_dir")" ] && [ "$(ls -A "$mirror_dir")" ]; then
    echo "All protobuf files have been generated and adjusted successfully!"
else
    echo "Error: Protobuf file generation or adjustment failed."
    exit 1
fi
