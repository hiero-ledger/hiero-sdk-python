#!/usr/bin/env python3
"""
Protobuf Generation Script
Features:
- Downloads Hedera protobufs for a given HAPI version from GitHub.
- Compiles the same proto sets as the original bash script, plus auxiliary dirs:
  * services/*.proto
  * services/auxiliary/tss/*.proto
  * services/auxiliary/hints/*.proto
  * services/auxiliary/history/*.proto
  * platform/event/*.proto
  * mirror/*.proto
- Preserves the directory structure in generated Python packages.
- Optionally emits type stubs (.pyi) and applies the same import adjustments.
- Normalizes mixed import styles into canonical, package-safe relative imports.
- Ensures generated packages are importable on all OSes (__init__.py injection).
- Cleans output directories safely (deduplicated) before regeneration.
- Logging:
  * INFO for stage summaries and rewrite totals.
  * DEBUG for useful counts.
  * TRACE (custom) for verbose details such as per-file rewrites and protoc args.
Run: python generate_proto.py -vv or with trace logs: python generate_proto.py -vvv
"""
import logging
import shutil
import tarfile
import urllib.request
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

VERSION="v0.66.0"
SOURCES = [
    {
        "name": "hedera-protobufs",
        "url": "https://github.com/hashgraph/hedera-protobufs",
        "version": VERSION,
        "strip_count": 1,
        "modules": ("mirror",) # Fixed: tuple needs trailing comma if single element
    },
    {
        "name": "hiero-consensus-node",
        "url": "https://github.com/hiero-ledger/hiero-consensus-node",
        "version": VERSION,
        "strip_count": 6,   
        "modules": ("services", "platform", "fee", "sdk", "block", "streams", "blocks")
    }
]

OUTPUT_DIR="src/hiero_sdk_python/hapi"
CACHE_DIR=".protos"

@dataclass
class Config:
    name: str
    url: str
    version: str
    strip_count: int 
    modules: tuple = field(default_factory=tuple)

def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1: level = logging.INFO
    elif verbosity >= 2: level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

def download_protos(config: Config, cache_path: Path) -> None:
    logging.info(f"Downloading {config.name} {config.version}...")
    url = f"{config.url}/archive/refs/tags/{config.version}.tar.gz"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            with tarfile.open(fileobj=resp, mode="r|gz") as tar:
                for member in tar:
                    parts = Path(member.name).parts
                    if len(parts) <= config.strip_count: continue
                    member.name = "/".join(parts[config.strip_count:])
                    if any(member.name.startswith(p) for p in config.modules):
                        tar.extract(member, path=cache_path)
    except Exception as e:
        raise RuntimeError(f"Download failed for {config.name}: {e}")

def patch_proto_imports(proto_root: Path):
    """
    Fixes broken legacy imports where files import 'basic_types.proto' 
    instead of 'services/basic_types.proto'.
    """
    logging.info("Patching proto files for consistent import paths...")
    
    # Map of common broken imports found in mirror/platform protos
    replacements = {
        'import "basic_types.proto";': 'import "services/basic_types.proto";',
        'import "timestamp.proto";': 'import "services/timestamp.proto";',
        'import "consensus_submit_message.proto";': 'import "services/consensus_submit_message.proto";',
        'import "response_code.proto";': 'import "services/response_code.proto";',
        'import "query.proto";': 'import "services/query.proto";',
        'import "transaction.proto";': 'import "services/transaction.proto";',
        'import "transaction_response.proto";': 'import "services/transaction_response.proto";',
        # Fix for platform/event specific error
        'import "event/state_signature_transaction.proto";': 'import "platform/event/state_signature_transaction.proto";',
    }

    for proto_file in proto_root.rglob("*.proto"):
        content = proto_file.read_text()
        new_content = content
        
        for broken, fixed in replacements.items():
            new_content = new_content.replace(broken, fixed)
        
        if "platform" in proto_file.parts:
            new_content = re.sub(r'import "event/', 'import "platform/event/', new_content)

        if new_content != content:
            proto_file.write_text(new_content)

def run_protoc(proto_root: Path, output_root: Path) -> None:
    from grpc_tools import protoc
    import grpc_tools
    google_include = str(Path(grpc_tools.__file__).parent / "_proto")
    all_protos = [p.as_posix() for p in proto_root.rglob("*.proto")]

    args = [
        "protoc",
        f"-I{proto_root.as_posix()}",
        f"-I{google_include}",
        f"--python_out={output_root.as_posix()}",
        f"--grpc_python_out={output_root.as_posix()}",
        f"--pyi_out={output_root.as_posix()}",
    ]
    args.extend(all_protos)
    if protoc.main(args) != 0:
        raise RuntimeError("protoc failed to generate proto files")

def fix_imports(output_root: Path):
    local_packages = {p.name for p in output_root.iterdir() if p.is_dir()}
    pattern = re.compile(r"^(?P<type>from|import)\s+(?P<path>" + "|".join(local_packages) + r")(?P<suffix>[\w\.]*)")

    for py_file in output_root.rglob("*.py*"):
        if py_file.name == "__init__.py": continue
        depth = len(py_file.relative_to(output_root).parents) - 1
        dots = "." * (depth + 1)
        lines = py_file.read_text().splitlines()
        new_lines = []

        for line in lines:
            match = pattern.match(line)
            if match:
                ptype, ppath, psuffix = match.group('type'), match.group('path'), match.group('suffix')
                full_module = ppath + psuffix
                if ptype == "from":
                    remainder = line.split("import", 1)[1].strip()
                    line = f"from {dots}{full_module} import {remainder}"
                elif ptype == "import":
                    if " as " in line:
                        module_parts = full_module.rsplit(".", 1)
                        alias = line.split(" as ", 1)[1].strip()
                        line = f"from {dots}{module_parts[0]} import {module_parts[1]} as {alias}" if len(module_parts) > 1 else f"from {dots} import {module_parts[0]} as {alias}"
                    else:
                        module_parts = full_module.rsplit(".", 1)
                        line = f"from {dots}{module_parts[0]} import {module_parts[1]}" if len(module_parts) > 1 else f"from {dots} import {module_parts[0]}"
            new_lines.append(line)
        py_file.write_text("\n".join(new_lines) + "\n")

def main():
    setup_logging(1)
    cache_path = Path(CACHE_DIR)
    out_path = Path(OUTPUT_DIR)

    if cache_path.exists(): shutil.rmtree(cache_path)
    if out_path.exists(): shutil.rmtree(out_path)
    cache_path.mkdir(parents=True)
    out_path.mkdir(parents=True)

    for src_data in SOURCES:
        src = Config(**src_data)
        download_protos(src, cache_path)

    patch_proto_imports(cache_path)
    
    logging.info("Running protoc...")
    run_protoc(cache_path, out_path)
    
    logging.info("Fixing imports...")
    fix_imports(out_path)
    
    for d in [out_path, *out_path.rglob("*")]:
        if d.is_dir(): (d / "__init__.py").touch()

    print(f"✅ Successfully merged and generated HAPI at {out_path}")

if __name__ == "__main__":
    main()