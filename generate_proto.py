#!/usr/bin/env python3
"""
Generate Hiero protobuf Python files from Hedera's hedera-protobufs repo.
Works on Windows, macOS, and Linux.

Usage (locally or in CI):
    python generate_proto.py
"""

import os
import sys
import shutil
import subprocess
import tarfile
import re
import urllib.request
from pathlib import Path

# Configure your directories and versions
HAPI_VERSION = "v0.57.3"
PROTOS_DIR = Path(".protos")
SERVICES_DIR = Path("src/hiero_sdk_python/hapi/services")
MIRROR_DIR = Path("src/hiero_sdk_python/hapi/mirror")


def clean_and_prepare_directories():
    """Remove old directories and create the required folder structure."""
    print("Setting up directories...")

    # 1) Clear .protos dir
    if PROTOS_DIR.is_dir():
        shutil.rmtree(PROTOS_DIR)
    PROTOS_DIR.mkdir(parents=True, exist_ok=True)

    # 2) Clear services and mirror dirs
    if SERVICES_DIR.is_dir():
        shutil.rmtree(SERVICES_DIR)
    if MIRROR_DIR.is_dir():
        shutil.rmtree(MIRROR_DIR)

    # 3) Recreate needed structure
    (SERVICES_DIR / "auxiliary" / "tss").mkdir(parents=True, exist_ok=True)
    (SERVICES_DIR / "event").mkdir(parents=True, exist_ok=True)
    MIRROR_DIR.mkdir(parents=True, exist_ok=True)

    # 4) Create __init__.py placeholders
    (SERVICES_DIR / "__init__.py").touch()
    (MIRROR_DIR / "__init__.py").touch()


def download_and_extract_protos():
    """Download and extract the protobuf tar for the specified HAPI_VERSION."""
    print(f"Downloading Hiero protobufs version {HAPI_VERSION}...")

    url = f"https://github.com/hashgraph/hedera-protobufs/archive/refs/tags/{HAPI_VERSION}.tar.gz"
    tarball_path = PROTOS_DIR / "hedera-protobufs.tar.gz"

    # Download .tar.gz
    with urllib.request.urlopen(url) as response, open(tarball_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

    print(f"Extracting tarball to {PROTOS_DIR}...")
    with tarfile.open(tarball_path, mode="r:gz") as tar_ref:
        for member in tar_ref.getmembers():
            path_parts = member.name.split(os.sep)
            if len(path_parts) > 1:
                new_path = os.sep.join(path_parts[1:])
            else:
                continue
            member.name = new_path
            if member.name:
                tar_ref.extract(member, path=PROTOS_DIR)

    tarball_path.unlink(missing_ok=True)

    for child in PROTOS_DIR.iterdir():
        if child.name not in ("platform", "services", "mirror"):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def run_protoc_for_services():
    """
    Compile 'services' and 'platform' protobuf files into Python files
    inside the services directory.
    """
    print("Compiling service and platform protobuf files...")

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={PROTOS_DIR / 'platform'}",
        f"--proto_path={PROTOS_DIR / 'services'}",
        f"--pyi_out={SERVICES_DIR}",
        f"--python_out={SERVICES_DIR}",
        f"--grpc_python_out={SERVICES_DIR}",
        *(str(p) for p in (PROTOS_DIR / "services").glob("*.proto")),
        *(str(p) for p in (PROTOS_DIR / "services" / "auxiliary" / "tss").glob("*.proto")),
        *(str(p) for p in (PROTOS_DIR / "platform" / "event").glob("*.proto")),
    ]

    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        print("Failed to compile service & platform protos:")
        print(completed.stderr.decode())
        sys.exit(1)


def adjust_imports_services():
    """
    Adjust the imports in the compiled Python files for 'services' & 'platform'
    to ensure relative paths are correct.
    """
    print("Adjusting imports for service and platform protobuf files...")

    for py_file in SERVICES_DIR.rglob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 1) Lines that start with "import something_pb2 as something__pb2" -> prefix 'from . '
        content = re.sub(
            r'^(import .*_pb2 as .*__pb2)',
            r'from . \1',
            content,
            flags=re.MULTILINE
        )

        # 2) Lines that start with "from auxiliary.tss" -> "from .auxiliary.tss"
        content = re.sub(
            r'^from auxiliary\.tss',
            'from .auxiliary.tss',
            content,
            flags=re.MULTILINE
        )

        # 3) Lines that start with "from event" -> "from .event"
        content = re.sub(
            r'^from event',
            'from .event',
            content,
            flags=re.MULTILINE
        )

        with open(py_file, "w", encoding="utf-8") as f:
            f.write(content)


def run_protoc_for_mirror():
    """
    Compile 'mirror' protobuf files into Python files inside the mirror directory.
    """
    print("Compiling mirror protobuf files...")

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={PROTOS_DIR / 'mirror'}",
        f"--proto_path={PROTOS_DIR / 'services'}",
        f"--python_out={MIRROR_DIR}",
        f"--grpc_python_out={MIRROR_DIR}",
        *(str(p) for p in (PROTOS_DIR / "mirror").glob("*.proto")),
    ]

    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        print("Failed to compile mirror protos:")
        print(completed.stderr.decode())
        sys.exit(1)


def adjust_imports_mirror():
    """
    Adjust the imports in the compiled Python files for 'mirror' to ensure paths
    reference the correct modules (services vs mirror).
    """
    print("Adjusting imports for mirror protobuf files...")
    for py_file in MIRROR_DIR.rglob("*.py"):
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(
            r'^import basic_types_pb2 as',
            'import hiero_sdk_python.hapi.services.basic_types_pb2 as',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^import timestamp_pb2 as',
            'import hiero_sdk_python.hapi.services.timestamp_pb2 as',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^import consensus_submit_message_pb2 as',
            'import hiero_sdk_python.hapi.services.consensus_submit_message_pb2 as',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^import consensus_service_pb2 as',
            'import hiero_sdk_python.hapi.mirror.consensus_service_pb2 as',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^import mirror_network_service_pb2 as',
            'import hiero_sdk_python.hapi.mirror.mirror_network_service_pb2 as',
            content,
            flags=re.MULTILINE
        )

        with open(py_file, "w", encoding="utf-8") as f:
            f.write(content)


def verify_generation_success():
    """Ensure protobuf files have been generated for both services and mirror."""
    if any(SERVICES_DIR.iterdir()) and any(MIRROR_DIR.iterdir()):
        print("All protobuf files have been generated and adjusted successfully!")
    else:
        print("Error: Protobuf file generation or adjustment failed.")
        sys.exit(1)


def main():
    """Main entry point."""
    clean_and_prepare_directories()
    download_and_extract_protos()
    run_protoc_for_services()
    adjust_imports_services()
    run_protoc_for_mirror()
    adjust_imports_mirror()
    verify_generation_success()


if __name__ == "__main__":
    main()
