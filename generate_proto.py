#!/usr/bin/env python3
"""
Protobuf Generation Script (with graceful dependency check)

- Downloads Hedera protobufs for a given HAPI version
- Compiles the same proto sets as the original bash script, plus aux dirs:
  * services/*.proto
  * services/auxiliary/tss/*.proto
  * services/auxiliary/hints/*.proto
  * services/auxiliary/history/*.proto
  * platform/event/*.proto
  * mirror/*.proto
- Preserves directory structure in the generated Python packages
- Normalizes mixed import styles into canonical paths to avoid duplicates
- Adjusts generated imports to be package-safe on all OSes
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set, Tuple
from urllib.error import URLError
from urllib.parse import urlparse
from grpc_tools import protoc

# -------------------- Defaults --------------------

DEFAULT_HAPI_VERSION = "v0.64.3"
DEFAULT_PROTOS_DIR = ".protos"
DEFAULT_OUTPUT = "src/hiero_sdk_python/hapi"

SCRIPT_DIR = Path(__file__).resolve().parent

# -------------------- Config --------------------


@dataclass(frozen=True)
class Config:
    hapi_version: str
    protos_dir: Path
    services_out: Path
    mirror_out: Path
    pyi_out: bool = True


# -------------------- CLI --------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Python protobuf files from Hedera proto definitions."
    )
    parser.add_argument(
        "--hapi-version",
        default=DEFAULT_HAPI_VERSION,
        help=f"Hedera protobuf version (default: {DEFAULT_HAPI_VERSION})",
    )
    parser.add_argument(
        "--protos-dir",
        default=DEFAULT_PROTOS_DIR,
        help=f"Directory for downloaded proto files (default: {DEFAULT_PROTOS_DIR})",
    )
    parser.add_argument(
        "--services-output",
        default=DEFAULT_OUTPUT,
        help="Output directory for services (default: %(default)s)",
    )
    parser.add_argument(
        "--mirror-output",
        default=DEFAULT_OUTPUT,
        help="Output directory for mirror (default: %(default)s)",
    )
    parser.add_argument(
        "--no-pyi",
        action="store_true",
        help="Do not emit .pyi stubs from protoc.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv).",
    )
    return parser.parse_args()


def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def resolve_path(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else (SCRIPT_DIR / q)


# -------------------- Dependency check --------------------


def ensure_grpc_tools() -> None:
    try:
        import grpc_tools  # noqa: F401
    except Exception as exc:  # pragma: no cover
        msg = (
            "Missing dependency: grpcio-tools\n"
            "  Using uv:    uv add grpcio-tools\n"
            f"  Using pip:   {sys.executable} -m pip install grpcio-tools"
        )
        logging.error(msg)
        raise SystemExit(1) from exc


# -------------------- Download & extract --------------------


def is_safe_tar_member(member: tarfile.TarInfo, base: Path) -> bool:
    name = member.name
    if not name or name.startswith("/"):
        return False
    # Prevent traversal like ../../etc/passwd
    if ".." in Path(name).parts:
        return False
    dest = (base / name).resolve()
    try:
        dest.relative_to(base.resolve())
    except ValueError:
        return False
    return True


def safe_extract_tar_stream(response, dest: Path) -> None:
    """Stream-extract a GitHub tgz, stripping the top-level folder safely."""
    with tarfile.open(fileobj=response, mode="r|gz") as tar:
        for member in tar:
            parts = Path(member.name).parts
            member.name = "/".join(parts[1:]) if len(parts) > 1 else ""
            if not member.name:
                continue
            if not is_safe_tar_member(member, dest):
                raise RuntimeError(f"Unsafe path in archive: {member.name}")
            tar.extract(member, path=dest)  # nosec B202 - path validated by is_safe_tar_member

def validate_url_and_version(url: str, hapi_version: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise RuntimeError(f"Refusing to fetch from non-https or unexpected host: {url}")

    if not re.fullmatch(r"v\d+\.\d+\.\d+", hapi_version):
        raise RuntimeError(f"Unexpected HAPI tag format: {hapi_version}")


def download_and_setup_protos(hapi_version: str, protos_dir: Path) -> None:
    logging.info("Downloading Hedera protobufs version %s ...", hapi_version)
    if protos_dir.exists():
        shutil.rmtree(protos_dir)
    protos_dir.mkdir(parents=True, exist_ok=True)

    url = (
        "https://github.com/hashgraph/hedera-protobufs/"
        f"archive/refs/tags/{hapi_version}.tar.gz"
    )
    validate_url_and_version(url, hapi_version)

    try:
        with urllib.request.urlopen(url, timeout=30) as resp: # nosec B310
            safe_extract_tar_stream(resp, protos_dir)
    except URLError as e:
        raise RuntimeError(f"Failed to download protobuf files: {e}") from e
    except (tarfile.TarError, OSError) as e:
        raise RuntimeError(f"Failed to extract protobuf files: {e}") from e

    # Keep only platform, services, mirror
    for item in list(protos_dir.iterdir()):
        if item.is_dir() and item.name not in {"platform", "services", "mirror"}:
            shutil.rmtree(item)

    logging.info("Protobufs ready at %s", protos_dir)

# -------------------- Filesystem helpers --------------------


def clean_and_prepare_output_dirs(*dirs: Path) -> None:
    for d in dirs:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)


def ensure_subpackages(base: Path, subdirs: Iterable[Path]) -> None:
    for p in subdirs:
        (base / p).mkdir(parents=True, exist_ok=True)


def create_init_files(*roots: Path) -> None:
    for root in roots:
        for p in [root, *root.rglob("*")]:
            if p.is_dir():
                (p / "__init__.py").touch(exist_ok=True)


def log_generated_files(output_dir: Path) -> None:
    print(f"\n📂 Generated compiled proto files in {output_dir}:")
    cwd = Path.cwd()
    for f in sorted(output_dir.rglob("*.py")):
        try:
            rel = f.relative_to(cwd)
        except ValueError:
            rel = f
        print(f"  - {rel}")


# -------------------- Protoc invocation --------------------
def run_protoc(
    proto_paths: List[Path],
    out_py: Path,
    out_grpc: Path,
    files: List[Path],
    pyi_out: bool = False,
) -> None:
    if not files:
        logging.info("No .proto files to compile (skipping).")
        return

    # Add grpc_tools' bundled google protos include path
    try:
        # setuptools/pkg_resources works with grpc_tools wheels
        from pkg_resources import resource_filename
        google_include = resource_filename("grpc_tools", "_proto")
    except Exception as _:
        # Fallback for environments without pkg_resources
        import importlib_resources  # type: ignore
        google_include = str(importlib_resources.files("grpc_tools").joinpath("_proto"))

    args: list[str] = ["protoc"]
    # 1) our temp normalized include(s)
    for pp in proto_paths:
        args += ["-I", str(pp)]
    # 2) google well-known types include
    args += ["-I", google_include]

    args += ["--python_out", str(out_py), "--grpc_python_out", str(out_grpc)]
    if pyi_out:
        args += ["--pyi_out", str(out_py)]
    args += [str(f) for f in files]

    logging.debug("protoc args: %s", " ".join(args))
    from grpc_tools import protoc
    code = protoc.main(args)
    if code != 0:
        raise RuntimeError(f"protoc failed with exit code {code}")

# -------------------- Import normalization for .proto --------------------


def rewrite_import_line(line: str, src_root: Path) -> str:
    """
    Normalize an 'import "..."' line to a canonical path:
      - leave google/ imports
      - event/...  -> platform/event/...
      - unqualified X.proto -> services/X.proto if exists, else platform/X.proto
    """
    m = re.match(r'\s*import\s+"([^"]+)"\s*;', line)
    if not m:
        return line
    target = m.group(1)

    # Already qualified or google include
    if target.startswith(("google/", "services/", "platform/", "mirror/")):
        return line

    if target.startswith("event/"):
        return line.replace(target, f"platform/{target}")

    if "/" not in target:
        if (src_root / "services" / target).exists():
            return line.replace(target, f"services/{target}")
        if (src_root / "platform" / target).exists():
            return line.replace(target, f"platform/{target}")

    return line


def parse_import_line(line: str, src_root: Path) -> tuple[str, Path | None]:
    """Return (possibly rewritten) line and a dependency Path (or None)."""
    if "import " not in line or ".proto" not in line:
        return line, None
    new_line = rewrite_import_line(line, src_root)
    m = re.match(r'\s*import\s+"([^"]+)"\s*;', new_line)
    if not m:
        return new_line, None
    target = m.group(1)
    if target.startswith("google/"):
        return new_line, None
    dep_rel = Path(target)
    return (new_line, dep_rel if (src_root / dep_rel).exists() else None)


def collect_and_normalize(
    src_root: Path,
    rel: Path,
    visited: Set[Path],
    tmp_root: Path,
) -> None:
    """
    Recursively copy `rel` into tmp_root and normalize its imports; follow deps.
    """
    if rel in visited:
        return
    visited.add(rel)

    src = src_root / rel
    if not src.exists():
        return

    dst = tmp_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)

    deps: list[Path] = []
    lines = src.read_text(encoding="utf-8").splitlines(True)
    out_lines: list[str] = []

    for line in lines:
        new_line, dep = parse_import_line(line, src_root)
        out_lines.append(new_line)
        if dep is not None:
            deps.append(dep)

    dst.write_text("".join(out_lines), encoding="utf-8")

    for d in deps:
        collect_and_normalize(src_root, d, visited, tmp_root)


def normalize_tree(src_root: Path, files: List[Path]) -> Tuple[Path, List[Path]]:
    """
    Build a temp tree containing `files` and their imported deps (non-google),
    with imports normalized to a single canonical path.
    Returns (temp_root, relative_paths_in_temp_for_original_files).
    """
    tmp = Path(tempfile.mkdtemp(prefix="protos_norm_"))
    visited: Set[Path] = set()
    for rel in files:
        collect_and_normalize(src_root, rel, visited, tmp)
    return tmp, files


# -------------------- File list builders --------------------


def service_and_platform_files(protos_root: Path) -> List[Path]:
    services = protos_root / "services"
    platform = protos_root / "platform"

    globs = [
        services.glob("*.proto"),
        (services / "auxiliary" / "tss").glob("*.proto"),
        (services / "auxiliary" / "hints").glob("*.proto"),
        (services / "auxiliary" / "history").glob("*.proto"),
        (services / "state" / "hints").glob("*.proto"),
        (services / "state" / "history").glob("*.proto"),
        (platform / "event").glob("*.proto"),
    ]

    files = [f for g in globs for f in sorted(g)]

    rel_files: List[Path] = []
    for f in files:
        if str(f).startswith(str(services)):
            rel_files.append(Path("services") / f.relative_to(services))
        elif str(f).startswith(str(platform)):
            rel_files.append(Path("platform") / f.relative_to(platform))
    return rel_files


def mirror_files(protos_root: Path) -> List[Path]:
    mirror = protos_root / "mirror"
    return [Path("mirror") / f.relative_to(mirror) for f in sorted(mirror.glob("*.proto"))]


# -------------------- Compile groups --------------------


def compile_services_and_platform(protos_root: Path, services_out: Path, pyi_out: bool) -> None:
    rel_files = service_and_platform_files(protos_root)
    temp_root, norm_rel_files = normalize_tree(protos_root, rel_files)
    try:
        run_protoc(
            proto_paths=[temp_root],
            out_py=services_out,
            out_grpc=services_out,
            files=norm_rel_files,
            pyi_out=pyi_out,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def compile_mirror(protos_root: Path, mirror_out: Path) -> None:
    rel_files = mirror_files(protos_root)
    temp_root, norm_rel_files = normalize_tree(protos_root, rel_files)
    try:
        run_protoc(
            proto_paths=[temp_root],
            out_py=mirror_out,
            out_grpc=mirror_out,
            files=norm_rel_files,
            pyi_out=False,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


# -------------------- Post-generation Python import fixups --------------------
def adjust_python_imports(services_dir: Path, mirror_dir: Path) -> None:
    service_root_modules = {f.stem for f in services_dir.glob("*_pb2.py")}

    # --- Services tree ---
    for py in services_dir.rglob("*.py"):
        if py.name == "__init__.py":
            continue
        content = py.read_text(encoding="utf-8")

        content = re.sub(r"^\s*import (\w+_pb2) as", r"from . import \1 as",
                         content, flags=re.MULTILINE)

        content = re.sub(r"^\s*from\s+services\s+import\s+(\w+_pb2)\s+as",
                         r"from . import \1 as", content, flags=re.MULTILINE)
        content = re.sub(r"^\s*from\s+services\s+import\s+(\w+_pb2)\b",
                         r"from . import \1", content, flags=re.MULTILINE)

        content = re.sub(
            r"^\s*from\s+services\.((?:\w+\.)*\w+)\s+import\s+(\w+_pb2)(\s+as\b)?",
            r"from .\1 import \2\3", content, flags=re.MULTILINE,
        )
        content = re.sub(
            r"^\s*import\s+services\.((?:\w+\.)*)(\w+_pb2)\s+as",
            r"from .\1 import \2 as", content, flags=re.MULTILINE,
        )
        content = re.sub(
            r"^\s*import\s+services\.((?:\w+\.)*)(\w+_pb2)\b",
            r"from .\1 import \2", content, flags=re.MULTILINE,
        )

        content = re.sub(r"^\s*from\s+auxiliary\.tss",     r"from .auxiliary.tss",     content, flags=re.MULTILINE)
        content = re.sub(r"^\s*from\s+auxiliary\.hints",   r"from .auxiliary.hints",   content, flags=re.MULTILINE)
        content = re.sub(r"^\s*from\s+auxiliary\.history", r"from .auxiliary.history", content, flags=re.MULTILINE)

        content = re.sub(r"^\s*from\s+event\s+import\s+(\w+_pb2)(\s+as\b)?",
                         r"from ..platform.event import \1\2", content, flags=re.MULTILINE)
        content = re.sub(r"^\s*from\s+platform\.event\s+import\s+(\w+_pb2)(\s+as\b)?",
                         r"from ..platform.event import \1\2", content, flags=re.MULTILINE)

        rel   = py.relative_to(services_dir)
        depth = len(rel.parent.parts)  
        dots  = "." * (depth + 1) 

        def repl_dot_state(m: re.Match) -> str:
            tail  = m.group(1) or ""
            mod   = m.group(2)
            alias = m.group(3) or ""
            return f"from {dots}state{tail} import {mod}{alias}"
        content = re.sub(r"^\s*from\s+\.\s*state(\.[\w\.]+)?\s+import\s+(\w+_pb2)(\s+as\b)?",
                         repl_dot_state, content, flags=re.MULTILINE)

        def repl_abs_state(m: re.Match) -> str:
            tail  = m.group(1) or ""
            mod   = m.group(2)
            alias = m.group(3) or ""
            return f"from {dots}state{tail} import {mod}{alias}"
        content = re.sub(r"^\s*from\s+services\.state(\.[\w\.]+)?\s+import\s+(\w+_pb2)(\s+as\b)?",
                         repl_abs_state, content, flags=re.MULTILINE)

        def repl_from_dot_local(m: re.Match) -> str:
            mod   = m.group(1)
            alias = m.group(2) or ""
            if mod in service_root_modules:
                return f"from {dots} import {mod}{alias}"
            return m.group(0)
        content = re.sub(r"^\s*from\s+\.\s+import\s+(\w+_pb2)(\s+as\s+\w+)?\s*$",
                         repl_from_dot_local, content, flags=re.MULTILINE)

        py.write_text(content, encoding="utf-8")

    # --- Mirror tree ---
    mirror_modules  = {f.stem for f in mirror_dir.rglob("*_pb2.py")}
    service_modules = {f.stem for f in services_dir.rglob("*_pb2.py")}

    for py in mirror_dir.rglob("*.py"):
        if py.name == "__init__.py":
            continue
        content = py.read_text(encoding="utf-8")

        def repl_import(m: re.Match) -> str:
            mod = m.group(1)
            if mod in mirror_modules:
                return f"from . import {mod} as"
            if mod in service_modules:
                return f"from ..services import {mod} as"
            return m.group(0)
        content = re.sub(r"^\s*import (\w+_pb2) as", repl_import, content, flags=re.MULTILINE)

        def repl_from_mirror(m: re.Match) -> str:
            mod = m.group(1)
            return f"from . import {mod} as" if mod in mirror_modules else m.group(0)
        content = re.sub(r"^\s*from\s+mirror\s+import\s+(\w+_pb2)\s+as",
                         repl_from_mirror, content, flags=re.MULTILINE)

        def repl_from_services(m: re.Match) -> str:
            mod = m.group(1)
            return f"from ..services import {mod} as" if mod in service_modules else m.group(0)
        content = re.sub(r"^\s*from\s+services\s+import\s+(\w+_pb2)\s+as",
                         repl_from_services, content, flags=re.MULTILINE)

        def repl_from_dot(m: re.Match) -> str:
            mod = m.group(1)
            return f"from ..services import {mod} as" if (mod in service_modules and mod not in mirror_modules) else m.group(0)
        content = re.sub(r"^\s*from\s+\.\s+import\s+(\w+_pb2)\s+as",
                         repl_from_dot, content, flags=re.MULTILINE)

        py.write_text(content, encoding="utf-8")


# -------------------- Main --------------------


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    ensure_grpc_tools()

    cfg = Config(
        hapi_version=args.hapi_version,
        protos_dir=resolve_path(args.protos_dir),
        services_out=resolve_path(args.services_output),
        mirror_out=resolve_path(args.mirror_output),
        pyi_out=not args.no_pyi,
    )

    # Fetch proto sources
    download_and_setup_protos(cfg.hapi_version, cfg.protos_dir)

    # Clean outputs & pre-create subpackages
    clean_and_prepare_output_dirs(cfg.services_out, cfg.mirror_out)
    ensure_subpackages(
        cfg.services_out,
        [
            Path("services"),
            Path("services/auxiliary/tss"),
            Path("services/auxiliary/hints"),
            Path("services/auxiliary/history"),
            Path("services/state/hints"),
            Path("services/state/history"),
            Path("platform/event"),
        ],
    )
    ensure_subpackages(cfg.mirror_out, [Path("mirror")])

    # Compile groups
    compile_services_and_platform(cfg.protos_dir, cfg.services_out, cfg.pyi_out)
    compile_mirror(cfg.protos_dir, cfg.mirror_out)
    log_generated_files(cfg.mirror_out)

    # Fix imports and make packages importable
    adjust_python_imports(cfg.services_out / Path("services"),
                      cfg.mirror_out / Path("mirror"))
    create_init_files(cfg.services_out, cfg.mirror_out)

    print("✅ All protobuf files have been generated and adjusted successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # one exit point
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
