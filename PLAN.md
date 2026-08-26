# Polovoxel Improvement Plan

Tracks the modernization of the Polovoxel Blender add-on: architecture, clean
code, docs, bug fixes, CLI packaging, and diagrams. Check items off as they
land so work can resume easily in a future session.

Legend: `[ ]` pending · `[x]` done

## Phase 0 — Analysis

- [x] 0.1 Bug & code-smell audit → `docs/BUGS.md`
- [x] 0.2 Target architecture design (layers, folder layout) → `docs/ARCHITECTURE.md`

## Phase 1 — Refactor into a clean-architecture package

- [x] 1.1 Restructure `polovoxel.py` into a `polovoxel/` add-on package
      (domain / infrastructure / operators / ui layers)
- [x] 1.2 Fix all bugs found in 0.1 during the refactor
- [x] 1.3 Apply clean-code pass (naming, docstrings, dead-code removal,
      consistent style)
- [x] 1.4 Sanity-check the package still imports/compiles cleanly

## Phase 2 — Documentation & tooling (depends on Phase 1)

- [x] 2.1 Testing tutorial → `docs/TESTING.md` (how to install/reload/debug
      the add-on inside Blender)
- [x] 2.2 CLI publish script → `scripts/publish.py` + docs → `docs/CLI.md`
- [x] 2.3 PlantUML architecture diagrams → `docs/architecture/*.puml`

## Phase 3 — Wrap-up

- [x] 3.1 Update `README.md` for the new package layout, docs links, and
      install/publish instructions
- [x] 3.2 Remove stale committed build artifact (`Polovoxel_0.0.2.zip`) now
      that `scripts/publish.py` regenerates it into `dist/`
- [x] 3.3 Final consistency check (all referenced files exist, `.py` files
      byte-compile, plan fully checked off)

## Notes

- Executed via background sub-agents (Workflow tool) to keep the main chat
  context small. Each phase's agent(s) update this file directly on
  completion.
- Source of truth for "is this done" is this file — re-read it before
  resuming work in a new session.
