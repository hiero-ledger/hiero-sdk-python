#!/usr/bin/env python3
"""
Step 3 Refactor: Token class parser, exporter, and controller
Enhanced to capture:
- Attributes from __init__
- Setters (set_/add_/remove_)
- All other methods, including private SDK helpers (_build_proto_body, _get_method, _from_proto)
- Optional proto conversion helpers (to_proto/from_proto)
"""

import ast
from pathlib import Path
from typing import Dict, List, Any


class TokenClassParser:
    """Parses .py files to extract token class attributes and methods."""

    def __init__(self, tokens_dir: Path):
        self.tokens_dir = tokens_dir
        self.errors: List[str] = []

    def extract_classes_from_file(self, file_path: Path) -> Dict[str, Dict[str, List[str]]]:
        """Extract classes with attributes and SDK methods from a Python file."""
        classes_info = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            self.errors.append(f"{file_path}: Failed to parse ({e})")
            return classes_info

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cls_name = node.name
                attributes = []
                setters = []
                others = []

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Capture __init__ args as attributes
                        if item.name == "__init__":
                            attributes = [arg.arg for arg in item.args.args if arg.arg != "self"]

                        # Setters / repeated-field helpers
                        elif item.name.startswith(("set_", "add_", "remove_")):
                            setters.append(item.name)

                        # All other methods (including private helpers starting with _)
                        else:
                            others.append(item.name)

                classes_info[cls_name] = {
                    "attributes": attributes,
                    "setters": setters,
                    "other_methods": others
                }

        return classes_info

    def parse_all(self) -> Dict[str, Any]:
        """Walk tokens directory and parse all classes."""
        all_classes_info = {}
        modules_seen = set()

        for py_file in self.tokens_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            module_name = py_file.stem
            modules_seen.add(module_name)
            class_info = self.extract_classes_from_file(py_file)
            if class_info:
                all_classes_info.update({f"{module_name}.{k}": v for k, v in class_info.items()})
            else:
                self.errors.append(f"{py_file}: No classes found or all failed parsing.")

        return {"modules": sorted(modules_seen), "classes": all_classes_info, "errors": self.errors}


class TokenClassExporter:
    """Handles writing the parsed data to files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_file = output_dir / "steps_3_token_classes_info_readable.py"
        self.error_file = output_dir / "steps_3_token_classes_errors.log"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_class_info(self, modules: List[str], classes_info: Dict[str, Any]) -> None:
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("# Auto-generated class info: attributes, setters, other methods\n\n")
            for mod in modules:
                f.write(f"from hiero_sdk_python.tokens import {mod}\n")
            f.write("\n")

            for full_cls_name, info in sorted(classes_info.items()):
                file_name = full_cls_name.split(".")[0] + ".py"
                f.write(f"# File: {file_name}\n")
                f.write(f"{full_cls_name} = {{\n")
                f.write("    'attributes': [\n")
                for attr in info['attributes']:
                    f.write(f"        '{attr}',\n")
                f.write("    ],\n")
                f.write("    'setters': [\n")
                for setter in info['setters']:
                    f.write(f"        '{setter}',\n")
                f.write("    ],\n")
                f.write("    'other_methods': [\n")
                for method in info['other_methods']:
                    f.write(f"        '{method}',\n")
                f.write("    ]\n")
                f.write("}\n\n")

    def write_error_log(self, errors: List[str]) -> None:
        with open(self.error_file, "w", encoding="utf-8") as f:
            if errors:
                f.write("# Errors encountered during parsing\n\n")
                for err in errors:
                    f.write(err + "\n")
            else:
                f.write("# No errors encountered\n")

    def export(self, modules, classes_info, errors):
        self.write_class_info(modules, classes_info)
        self.write_error_log(errors)
        print(f"✅ Class info written to: {self.output_file}")
        print(f"🪶 Errors (if any) written to: {self.error_file}")


class TokenClassExtractor:
    """Controller that ties everything together."""

    def __init__(self, project_root: Path):
        self.tokens_dir = project_root / "src" / "hiero_sdk_python" / "tokens"
        self.output_dir = project_root / "scripts" / "src_vs_proto"

    def run(self):
        parser = TokenClassParser(self.tokens_dir)
        exporter = TokenClassExporter(self.output_dir)

        print(f"🔍 Scanning token modules in {self.tokens_dir}...")
        result = parser.parse_all()

        exporter.export(result["modules"], result["classes"], result["errors"])
        print("✅ Done.")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    TokenClassExtractor(project_root).run()
