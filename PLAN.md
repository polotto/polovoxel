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

## Phase 5 — `usecases/` layer + factory (layering fix)

Requested after noticing `operators/` were importing `infrastructure/`
directly — a real violation of the dependency rule in
`docs/ARCHITECTURE.md`, not a hypothetical one.

- [x] 5.1 Add `usecases/` package: one use-case class per operator
      (`AddFirstVoxelUseCase`, `AddVoxelOnFaceUseCase`,
      `AddVoxelAtMouseUseCase`, `AddCuboidUseCase`), each orchestrating
      `domain/` + `infrastructure/` via a constructor-injected
      `mesh_infra` dependency
- [x] 5.2 Add `usecases/factory.py` (`UseCaseFactory`) to separate use-case
      *construction* (wiring the infra dependency) from *use* (operators
      calling `.execute(...)`)
- [x] 5.3 Strip `infrastructure/blender_mesh.py` down to pure bpy/bmesh
      adapters only — moved `add_voxel_on_selected_face`/
      `add_voxel_at_mouse` orchestration into `usecases/`, dropped its
      `domain/` import (no longer needed)
- [x] 5.4 Rewire all four `operators/*.py` to call `usecases/factory.py`
      instead of importing `domain/`/`infrastructure/` directly
- [x] 5.5 Update `docs/ARCHITECTURE.md` (package layout, dependency-rule
      diagram/prose, "why this counts as clean architecture" section) and
      `docs/architecture/*.puml` + `docs/architecture/README.md`'s embedded
      copies to match
- [x] 5.6 `python3 -m py_compile` all touched files; needs a live Blender
      smoke test (all four add actions + click-to-add) before being
      considered fully verified — not run in this session, no sandboxed
      Blender available

## Phase 6 — Repository port (Dependency Inversion for `usecases/`)

Requested as an immediate follow-up to Phase 5: `usecases/` still imported
`infrastructure/blender_mesh.py`'s functions directly, which is the same
layering shape as the bug Phase 5 fixed, one level down.

- [x] 6.1 Add `domain/mesh_repository.py`: `MeshRepository`, an `abc.ABC`
      port with abstract methods `create_cube`,
      `get_first_selected_face_center_location`, `get_face_under_mouse` —
      zero `bpy` imports, same testability guarantee as `domain/geometry.py`
- [x] 6.2 Convert `infrastructure/blender_mesh.py`'s free functions into
      `BlenderMeshRepository`, a class implementing `MeshRepository`
- [x] 6.3 Rewire the four `usecases/*.py` classes to depend on the abstract
      `MeshRepository` (constructor param renamed `mesh_infra` →
      `mesh_repo`, type-hinted) instead of the concrete infra module —
      use-case modules no longer import `infrastructure/` at all
- [x] 6.4 Update `usecases/factory.py` to construct one shared
      `BlenderMeshRepository` instance and inject it — the only file in
      `usecases/` still allowed to import `infrastructure/`
- [x] 6.5 Update `docs/ARCHITECTURE.md` (package layout, dependency-rule
      diagram/prose, "why this counts as clean architecture" section) and
      `docs/architecture/*.puml` + `docs/architecture/README.md`'s embedded
      copies to match
- [x] 6.6 `python3 -m py_compile` all touched files + verified
      `BlenderMeshRepository` implements every `MeshRepository` abstract
      method; still needs a live Blender smoke test before being
      considered fully verified — not run in this session, no sandboxed
      Blender available

## Notes

- Executed via background sub-agents (Workflow tool) to keep the main chat
  context small. Each phase's agent(s) update this file directly on
  completion.
- Source of truth for "is this done" is this file — re-read it before
  resuming work in a new session.
