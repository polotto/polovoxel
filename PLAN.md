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

## Phase 4 — Live-testing bug fixes (post-release)

Found and fixed through hands-on testing in real Blender after Phase 3
shipped — the original audit (0.1) couldn't catch these because the
features involved had never actually been exercised end-to-end before.
Each is documented in full in `docs/BUGS.md` #17–19.

- [x] 4.1 Material color never reached Material Preview/Rendered shading
      (`docs/BUGS.md` #17)
- [x] 4.2 No operator declared `bl_options = {'REGISTER', 'UNDO'}`,
      risking a native Blender crash on undo (`docs/BUGS.md` #18)
- [x] 4.3 "Enable add with click" never actually worked — redesigned from
      edit-mesh-selection-based to mouse raycast-based, fixing four
      compounding issues along the way (never invoked, restricted-context
      modal start, `context.area` unavailable for timer-started modals,
      off-face-center drift) (`docs/BUGS.md` #19)

See [`CLAUDE.md`](CLAUDE.md) for the process used to find and fix these —
the live-debugging protocol there is what future sessions should follow
for the next round of bugs, not just this plan file.

## Notes

- Executed via background sub-agents (Workflow tool) to keep the main chat
  context small. Each phase's agent(s) update this file directly on
  completion.
- Source of truth for "is this done" is this file — re-read it before
  resuming work in a new session.
