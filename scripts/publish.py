#!/usr/bin/env python3
"""Packaging script for the Polovoxel Blender add-on.

Builds an installable zip of the ``polovoxel/`` package (as expected by
Blender's "Install from File..." add-on installer) into ``dist/``.

Standard-library only: this script must run with the system Python 3,
outside of Blender's own bundled interpreter.

Usage (from the repo root):

    python3 scripts/publish.py                        # build dist/polovoxel_<version>.zip
    python3 scripts/publish.py --check                 # dry run, no files written
    python3 scripts/publish.py --version-bump patch     # bump version, then build
    python3 scripts/publish.py --output-dir build       # write the zip elsewhere

See docs/CLI.md for full documentation.
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "polovoxel"
INIT_FILE = SOURCE_DIR / "__init__.py"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "dist"

VERSION_BUMP_LEVELS = ("major", "minor", "patch")


class PublishError(Exception):
    """Raised for any expected failure; caught in main() and reported cleanly."""


def find_bl_info_and_version_node(source: str) -> tuple[dict, ast.Tuple]:
    """Parse ``source`` and return ``(bl_info dict, version-tuple AST node)``.

    Uses :mod:`ast` rather than executing the file, since ``polovoxel/__init__.py``
    imports ``bpy`` at module level, which is not available outside Blender.
    """
    try:
        tree = ast.parse(source, filename=str(INIT_FILE))
    except SyntaxError as exc:
        raise PublishError(f"Could not parse {INIT_FILE}: {exc}") from exc

    bl_info_dict_node = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "bl_info" in targets and isinstance(node.value, ast.Dict):
            bl_info_dict_node = node.value
            break

    if bl_info_dict_node is None:
        raise PublishError(f"Could not find a top-level 'bl_info = {{...}}' dict in {INIT_FILE}")

    version_node = None
    for key_node, value_node in zip(bl_info_dict_node.keys, bl_info_dict_node.values):
        if isinstance(key_node, ast.Constant) and key_node.value == "version":
            version_node = value_node
            break

    if version_node is None:
        raise PublishError(f"bl_info in {INIT_FILE} has no 'version' key")

    if not isinstance(version_node, ast.Tuple):
        raise PublishError(f"bl_info['version'] in {INIT_FILE} is not a tuple literal")

    try:
        bl_info = ast.literal_eval(bl_info_dict_node)
    except (ValueError, SyntaxError) as exc:
        raise PublishError(f"Could not evaluate bl_info in {INIT_FILE}: {exc}") from exc

    return bl_info, version_node


def read_version() -> tuple[tuple, ast.Tuple, str]:
    """Return ``(version_tuple, version_ast_node, source_text)`` read from disk."""
    if not INIT_FILE.is_file():
        raise PublishError(f"Add-on entry point not found: {INIT_FILE}")

    source = INIT_FILE.read_text(encoding="utf-8")
    bl_info, version_node = find_bl_info_and_version_node(source)

    version = bl_info.get("version")
    if not isinstance(version, tuple) or not all(isinstance(part, int) for part in version):
        raise PublishError(f"bl_info['version'] must be a tuple of ints, got: {version!r}")

    return version, version_node, source


def bump_version(version: tuple, level: str) -> tuple:
    if len(version) != 3:
        raise PublishError(
            f"Cannot apply --version-bump to a version with {len(version)} components "
            f"(expected 3): {version!r}"
        )
    major, minor, patch = version
    if level == "major":
        return (major + 1, 0, 0)
    if level == "minor":
        return (major, minor + 1, 0)
    if level == "patch":
        return (major, minor, patch + 1)
    raise PublishError(f"Unknown version bump level: {level!r}")


def write_bumped_version(source: str, version_node: ast.Tuple, new_version: tuple) -> str:
    """Return ``source`` with the bl_info version tuple text replaced by ``new_version``."""
    new_text = repr(tuple(new_version))
    lines = source.splitlines(keepends=True)

    start_line = version_node.lineno - 1
    end_line = version_node.end_lineno - 1

    if start_line == end_line:
        line = lines[start_line]
        lines[start_line] = line[: version_node.col_offset] + new_text + line[version_node.end_col_offset :]
    else:
        first = lines[start_line][: version_node.col_offset]
        last = lines[end_line][version_node.end_col_offset :]
        lines[start_line : end_line + 1] = [first + new_text + last]

    return "".join(lines)


def version_string(version: tuple) -> str:
    return ".".join(str(part) for part in version)


def iter_package_files(source_dir: Path):
    """Yield sorted absolute paths of files to include, skipping __pycache__ and .pyc files."""
    files = []
    for dirpath, dirnames, filenames in os.walk(source_dir):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for filename in filenames:
            if filename.endswith(".pyc"):
                continue
            files.append(Path(dirpath) / filename)
    return sorted(files)


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def build_zip(source_dir: Path, output_path: Path, package_name: str) -> int:
    """Write the zip and return the number of files included."""
    files = iter_package_files(source_dir)
    if not files:
        raise PublishError(f"No files found to package under {source_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            relative = file_path.relative_to(source_dir)
            arcname = Path(package_name) / relative
            zf.write(file_path, arcname=str(arcname))

    return len(files)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="publish.py",
        description="Package the Polovoxel Blender add-on into an installable zip.",
    )
    parser.add_argument(
        "--version-bump",
        choices=VERSION_BUMP_LEVELS,
        default=None,
        help="Bump the version in polovoxel/__init__.py's bl_info before packaging "
        "(major.minor.patch semantics) and persist the change to the file.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Directory to write the zip into (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry run: print what would be built without writing any files "
        "(including not persisting --version-bump).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        if not SOURCE_DIR.is_dir():
            raise PublishError(f"Add-on source folder not found: {SOURCE_DIR}")

        version, version_node, source = read_version()

        new_version = version
        if args.version_bump:
            new_version = bump_version(version, args.version_bump)

        output_dir = Path(args.output_dir).resolve() if args.output_dir else DEFAULT_OUTPUT_DIR
        package_name = SOURCE_DIR.name
        zip_filename = f"{package_name}_{version_string(new_version)}.zip"
        output_path = output_dir / zip_filename

        if args.check:
            files = iter_package_files(SOURCE_DIR)
            print("Dry run (--check): nothing was written.")
            if args.version_bump:
                print(f"Version:     {version_string(version)} -> {version_string(new_version)} (not persisted)")
            else:
                print(f"Version:     {version_string(version)}")
            print(f"Output path: {output_path}")
            print(f"File count:  {len(files)}")
            print("Zip size:    n/a (dry run)")
            return 0

        if args.version_bump:
            new_source = write_bumped_version(source, version_node, new_version)
            INIT_FILE.write_text(new_source, encoding="utf-8")
            print(f"Bumped version: {version_string(version)} -> {version_string(new_version)}")

        file_count = build_zip(SOURCE_DIR, output_path, package_name)
        zip_size = output_path.stat().st_size

        print("Build complete.")
        print(f"Version:     {version_string(new_version)}")
        print(f"Output path: {output_path}")
        print(f"File count:  {file_count}")
        print(f"Zip size:    {human_size(zip_size)}")
        return 0

    except PublishError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
