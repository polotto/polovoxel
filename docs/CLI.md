# CLI: packaging the add-on

`scripts/publish.py` packages the `polovoxel/` add-on source into a zip that
Blender's add-on installer can consume. It is a standard-library-only Python
3 script — it does not import `bpy`, so it runs with your system Python, not
Blender's bundled interpreter.

## Purpose

Blender installs add-ons from a zip whose top level is the add-on's package
folder. This script builds exactly that: a zip containing a single top-level
`polovoxel/` folder (mirroring `/Users/angelopolotto/GitHub/polovoxel/polovoxel/`),
with `__pycache__` directories and `.pyc` files excluded. It also reads the
add-on's version straight from `bl_info["version"]` in `polovoxel/__init__.py`
(instead of a hardcoded value), and can optionally bump that version before
packaging.

## Usage

Run from the repo root:

```sh
python3 scripts/publish.py [flags]
```

## Flags

### `--version-bump {major,minor,patch}`

Bumps the `version` tuple in `bl_info` (in `polovoxel/__init__.py`) using
major.minor.patch semantics, rewrites that file on disk, and then packages
the bumped version. A `minor` bump resets `patch` to `0`; a `major` bump
resets both `minor` and `patch` to `0`.

```sh
python3 scripts/publish.py --version-bump patch
# Bumped version: 0.1.0 -> 0.1.1
# Build complete.
# Version:     0.1.1
# Output path: /Users/angelopolotto/GitHub/polovoxel/dist/polovoxel_0.1.1.zip
# File count:  14
# Zip size:    9.7 KB
```

### `--output-dir <path>`

Writes the zip into `<path>` instead of the default `dist/` directory.
The directory is created if it doesn't exist.

```sh
python3 scripts/publish.py --output-dir build/
# ... Output path: build/polovoxel_0.1.0.zip
```

### `--check`

Dry run. Prints what would be built (version, output path, file count)
without writing anything — no zip is created and, importantly, a
`--version-bump` passed alongside `--check` is **not** persisted to
`polovoxel/__init__.py`.

```sh
python3 scripts/publish.py --check
# Dry run (--check): nothing was written.
# Version:     0.1.0
# Output path: /Users/angelopolotto/GitHub/polovoxel/dist/polovoxel_0.1.0.zip
# File count:  14
# Zip size:    n/a (dry run)
```

### `-h` / `--help`

Prints usage and exits.

```sh
python3 scripts/publish.py -h
```

## Output

With no flags, the script builds:

```
dist/polovoxel_<version>.zip
```

e.g. `dist/polovoxel_0.1.0.zip`. `dist/` is gitignored — the zip is a build
artifact, not something to commit. Inside the zip, the folder structure is:

```
polovoxel/
├── __init__.py
├── domain/...
├── infrastructure/...
├── operators/...
├── ui/...
└── keymaps.py
```

To install it: in Blender, go to **Edit > Preferences > Add-ons > Install...**
and pick the zip (or drag-and-drop it onto the Blender window), then enable
"Polovoxel" in the add-on list.

## Errors

The script exits with a non-zero status and a message on `stderr` for any
expected failure — e.g. the `polovoxel/` source folder is missing, or
`bl_info`/`bl_info["version"]` can't be found or parsed in
`polovoxel/__init__.py`.

## CI / release automation

Because it's a plain, dependency-free Python script with clear exit codes,
CI or a release process can call `python3 scripts/publish.py --version-bump patch`
(or similar) directly as a build step.
