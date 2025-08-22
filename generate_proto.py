#!/usr/bin/env python3
"""
Protobuf Generation Script

This script downloads Hedera protobuf files, processes them to fix imports,
and compiles them using protoc to generate Python protobuf files.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import List, Optional

DEFAULT_HAPI_VERSION = "v0.64.3"
DEFAULT_PROTOS_DIR = ".protos"
DEFAULT_SERVICES_OUTPUT = "src/hiero_sdk_python/hapi/services"
DEFAULT_MIRROR_OUTPUT = "src/hiero_sdk_python/hapi/mirror"


def main():
    """Main entry point for the protobuf generation script."""
    args = parse_args()

    try:
        # Step 1: Download and setup protobuf files
        protos_dir = Path(args.protos_dir)
        download_and_setup_protos(args.hapi_version, protos_dir)

        # Step 2: Clean the output directories
        services_output = Path(args.services_output)
        mirror_output = Path(args.mirror_output)
        clean_and_prepare_output_dirs(services_output, mirror_output)

        # Step 3: Process services/platform files
        services_source_dirs = [protos_dir / "services", protos_dir / "platform"]
        process_proto_files(services_source_dirs, services_output, "services")

        # Step 4: Process mirror files (with services dependencies)
        mirror_source_dirs = [protos_dir / "mirror"]
        process_mirror_files(mirror_source_dirs, services_source_dirs, mirror_output)

        # Step 5: Adjust Python imports
        adjust_python_imports(services_output, mirror_output)

        # Step 6: Create __init__.py files
        create_init_files(services_output, mirror_output)

        print("✅ All protobuf files have been generated successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def process_mirror_files(
    mirror_source_dirs: List[Path],
    services_source_dirs: List[Path],
    mirror_output: Path,
) -> None:
    """Process mirror proto files with their services dependencies."""
    print("Processing mirror files...")

    with tempfile.TemporaryDirectory() as services_temp_dir:
        # Create a temp services directory for mirror dependencies
        services_temp_path = Path(services_temp_dir)

        # Copy services/platform files for mirror dependencies
        copy_services_for_mirror(services_source_dirs, services_temp_path)

        # Process mirror files with services as additional proto paths
        process_proto_files(
            mirror_source_dirs,
            mirror_output,
            "mirror",
            additional_proto_paths=[services_temp_path],
        )


def copy_services_for_mirror(
    services_source_dirs: List[Path], services_temp_path: Path
) -> None:
    """Copy services/platform proto files to temp directory for mirror dependencies."""
    print("Copying services files for mirror dependencies...")

    for source_dir in services_source_dirs:
        if source_dir.exists():
            for proto_file in source_dir.rglob("*.proto"):
                content = proto_file.read_text(encoding="utf-8")
                fixed_content = fix_proto_imports(content)
                (services_temp_path / proto_file.name).write_text(
                    fixed_content, encoding="utf-8"
                )

    print(f"✅ Copied services files to temporary directory")


def clean_and_prepare_output_dirs(*output_dirs: Path) -> None:
    """
    Remove and recreate the given output directories.

    Args:
        *output_dirs (Path): One or more Path objects representing directories to clean and prepare.
    """
    for output_dir in output_dirs:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the protobuf generation script.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate Python protobuf files from Hedera proto definitions"
    )

    parser.add_argument(
        "--hapi-version",
        default=DEFAULT_HAPI_VERSION,
        help=f"Hedera protobuf version to use (default: {DEFAULT_HAPI_VERSION})",
    )
    parser.add_argument(
        "--protos-dir",
        default=DEFAULT_PROTOS_DIR,
        help=f"Directory containing proto files (default: {DEFAULT_PROTOS_DIR})",
    )

    parser.add_argument(
        "--services-output",
        default=DEFAULT_SERVICES_OUTPUT,
        help=f"Output directory for services (default: {DEFAULT_SERVICES_OUTPUT})",
    )
    parser.add_argument(
        "--mirror-output",
        default=DEFAULT_MIRROR_OUTPUT,
        help=f"Output directory for mirror (default: {DEFAULT_MIRROR_OUTPUT})",
    )

    return parser.parse_args()


def fix_proto_imports(content: str) -> str:
    """
    Change import statements in proto files to use only the filename,
    except for imports that start with "google/".
    """

    def repl(match):
        path = match.group(1)
        if path.startswith("google/"):
            return match.group(0)
        return f'import "{Path(path).name}"'

    return re.sub(r'import\s+"([^"]+\.proto)"', repl, content)


def process_proto_files(
    source_dirs: List[Path],
    output_dir: Path,
    proto_type: str,
    additional_proto_paths: Optional[List[Path]] = None,
) -> None:
    """
    Generate Python and gRPC code from proto files in the given source directories.

    Args:
        source_dirs (List[Path]): Directories containing .proto files to process.
        output_dir (Path): Directory where generated Python files will be written.
        proto_type (str): Type of proto files being processed (e.g., "services", "mirror").
        additional_proto_paths (Optional[List[Path]]): Extra directories to search for proto dependencies.

    Returns:
        None

    Raises:
        RuntimeError: If protoc fails to generate the files.
    """
    print(f"Processing {proto_type} proto files...")

    # Collect all proto files and their fixed content in memory
    proto_files_data = {}

    for source_dir in source_dirs:
        if source_dir.exists():
            for proto_file in source_dir.rglob("*.proto"):
                # Read and fix imports
                content = proto_file.read_text(encoding="utf-8")
                fixed_content = fix_proto_imports(content)
                proto_files_data[proto_file.name] = fixed_content

    if not proto_files_data:
        print(f"No {proto_type} proto files to process")
        return

    # Use temporary directory only for protoc execution
    with tempfile.TemporaryDirectory() as temp_protoc_dir:
        temp_path = Path(temp_protoc_dir)

        # Write fixed proto files to temp dir for protoc
        for filename, content in proto_files_data.items():
            (temp_path / filename).write_text(content, encoding="utf-8")

        # Build protoc command
        cmd = [
            "python",
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={temp_path}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
        ]

        # Add .pyi generation for services
        if proto_type == "services":
            cmd.append(f"--pyi_out={output_dir}")

        # Add additional proto paths for dependencies
        if additional_proto_paths:
            for path in additional_proto_paths:
                cmd.append(f"--proto_path={path}")

        # Add all proto files
        cmd.extend([str(temp_path / filename) for filename in proto_files_data.keys()])

        print(f"Generating {len(proto_files_data)} {proto_type} files...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("STDERR:", result.stderr)
            raise RuntimeError(f"protoc failed for {proto_type} files: {result.stderr}")

        print(f"✅ {proto_type.title()} protobuf generation completed")


def download_and_setup_protos(hapi_version: str, protos_dir: Path) -> None:
    """Download and extract Hedera protobuf files from GitHub."""
    print(f"Downloading Hedera protobufs version {hapi_version}...")

    # Clean up existing protos directory
    if protos_dir.exists():
        shutil.rmtree(protos_dir)
    protos_dir.mkdir(parents=True, exist_ok=True)

    # Download URL
    url = f"https://github.com/hashgraph/hedera-protobufs/archive/refs/tags/{hapi_version}.tar.gz"

    try:
        # Download the tar.gz file
        print(f"Downloading from: {url}")
        with urllib.request.urlopen(url) as response:
            # Extract directly to protos_dir with strip-components=1
            with tarfile.open(fileobj=response, mode="r|gz") as tar:
                # Extract all members but strip the top-level directory
                for member in tar:
                    # Skip the top-level directory (e.g., "hedera-protobufs-0.X.Y/")
                    if "/" in member.name:
                        # Remove the first directory component
                        member.name = "/".join(member.name.split("/")[1:])
                        if member.name:  # Don't extract empty names
                            tar.extract(member, path=protos_dir)

        print(f"✅ Downloaded and extracted to {protos_dir}")

        # Clean up unwanted directories, keep only platform, services, and mirror
        for item in protos_dir.iterdir():
            if item.is_dir() and item.name not in ["platform", "services", "mirror"]:
                shutil.rmtree(item)
                print(f"Removed unwanted directory: {item.name}")

        print("✅ Protobuf setup completed")

    except Exception as e:
        raise RuntimeError(f"Failed to download protobuf files: {e}")


def adjust_python_imports(services_dir: Path, mirror_dir: Path) -> None:
    """Adjust Python imports based on what was generated."""
    print("Adjusting Python imports...")

    # Adjust services imports
    for py_file in services_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()
        original_content = content

        # Convert absolute pb2 imports to relative imports
        content = re.sub(
            r"^import (\w+_pb2) as", r"from . import \1 as", content, flags=re.MULTILINE
        )

        if content != original_content:
            py_file.write_text(content)
            print(f"Adjusted imports in {py_file.relative_to(services_dir)}")

    for py_file in mirror_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()

        mirror_files = {f.stem for f in mirror_dir.glob("*_pb2.py")}

        # Remove mirror files from services files
        services_files = {f.stem for f in services_dir.glob("*_pb2.py")} - mirror_files

        # Find what this specific file actually imports
        import_matches = re.findall(r"^import (\w+_pb2) as", content, re.MULTILINE)

        for imported_module in import_matches:
            if imported_module in services_files:
                # It's a services module - redirect to ..services
                content = re.sub(
                    rf"^import {imported_module} as",
                    rf"from ..services import {imported_module} as",
                    content,
                    flags=re.MULTILINE,
                )
            elif imported_module in mirror_files:
                # It's a mirror module - make relative
                content = re.sub(
                    rf"^import {imported_module} as",
                    rf"from . import {imported_module} as",
                    content,
                    flags=re.MULTILINE,
                )

        py_file.write_text(content)


def create_init_files(*output_dirs: Path) -> None:
    """Ensure __init__.py exists in output_dir and all subdirectories."""
    for output_dir in output_dirs:
        for path in [output_dir, *output_dir.rglob("*")]:
            if path.is_dir():
                init_file = path / "__init__.py"
                init_file.touch(exist_ok=True)


if __name__ == "__main__":
    main()
