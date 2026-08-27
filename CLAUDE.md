# Polovoxel — project instructions

Polovoxel is a small Blender add-on (voxel-art cube placement) structured as
a clean-architecture Python package under `polovoxel/`. This file is the
process doc for working on it — read it before making changes, and follow
it the same way regardless of what the task is (bug fix, new feature,
refactor).

## Map of the docs

Don't duplicate content across docs — extend the right one instead:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the 4-layer design
  (`domain` → `infrastructure` → `operators` → `ui`) and the dependency
  rule between them
- [`docs/architecture/`](docs/architecture/) — PlantUML diagrams matching
  that architecture; update them if the layering changes
- [`docs/BUGS.md`](docs/BUGS.md) — the full bug audit, numbered findings
  with a summary table
- [`docs/TESTING.md`](docs/TESTING.md) — how to install/reload/debug the
  add-on inside Blender, including the reload caveats below
- [`docs/CLI.md`](docs/CLI.md) — `scripts/publish.py` packaging reference
- [`PLAN.md`](PLAN.md) — resumable checklist of what's done; re-read it
  before starting work in a new session so you know current state

## Architecture rule

`polovoxel/domain/` must never import `bpy`/`bmesh`/`bpy.ops` — it's pure
math (grid coordinates, material naming) so it stays unit-testable outside
Blender. Everything else depends inward on `domain`, never the reverse.
`infrastructure/` is the only layer allowed to touch `bpy.ops`/`bpy.data`/
`bmesh` directly. `operators/` are thin use-cases that call into
`infrastructure`/`domain`. `ui/` is presentation only (Panel/PropertyGroup).

This is a hobby-scale add-on, not an enterprise app — keep additions
proportional. Don't add config systems, plugin registries, or abstractions
for hypothetical future needs. A bug fix doesn't need surrounding cleanup.

## Verification — do this after every code change

Blender's Python modules (`bpy`, `bmesh`, `mathutils`) aren't importable
outside Blender, so a real functional test always requires the user to run
it live. But every `.py` file must still be checked for syntax errors
before you call anything done:

```bash
python3 -m py_compile <changed files>
```

This is the ceiling of what you can verify without the user's help — it
catches typos/syntax errors, nothing else. Don't skip it, and don't claim
a fix "should work" without having run it.

## Bug-tracking discipline

Every bug found — whether from a planned audit or discovered live via
testing — gets appended to `docs/BUGS.md` as a new numbered finding,
following the existing format exactly:

```markdown
### N. <one-line summary of the defect>
- **Location:** <file/function/line>
- **Severity:** High | Medium | Low
- **Evidence:** <code snippet showing the problem>
- **Failure scenario:** <concrete inputs/state → wrong output/crash, one paragraph>
- **Fix:** <what changed, and why>
```

Also add a row to the summary table at the bottom of the file. Never
renumber or delete existing findings — append only, so the file is a
running history. If a fix for one finding turns out to be incomplete (this
happens — see #19's four follow-ups), add a **Follow-up N** bullet under
the *same* finding describing what was learned and what changed, rather
than opening a new top-level finding for what's really the same bug.

## Live-debugging protocol (Blender-specific)

You cannot run Blender yourself in this environment — there is no
sandboxed Blender instance available. When a fix doesn't visibly work in
the user's live session, **do not stack another speculative fix on top of
the last one.** That produced several dead ends in this project's history
before the real root causes were found (see `docs/BUGS.md` #19's
follow-ups 1–4 for a worked example: two plausible-but-wrong theories were
tried and correctly ruled out with real evidence before the actual cause —
`context.area` being `None` for timer-started modals — was found).

Instead, in order:

1. Form one specific, falsifiable hypothesis for why the observed behavior
   is happening.
2. Get real evidence before changing more code. Ask the user to launch
   Blender from Terminal so Python output is visible:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender
   ```
   (see `docs/TESTING.md` §3). If the existing code doesn't already report
   enough to confirm/deny the hypothesis, add a temporary, unconditional
   `print()` or `self.report()` at the relevant point, ask the user to
   reproduce, and read back the exact output — not a paraphrase.
3. Only once the evidence confirms the hypothesis, make the real fix.
4. Remove any temporary debug instrumentation added in step 2 once the fix
   is confirmed — don't leave debug prints in shipped code.
5. Document the finding in `docs/BUGS.md` per the format above, including
   what evidence confirmed it (this makes the next session's job easier if
   a related bug shows up later).

For operator code specifically: prefer `self.report({'WARNING'}/{'ERROR'}, ...)`
over silently returning `{'PASS_THROUGH'}`/`{'CANCELLED'}` on a failure
path a user could hit — a silent failure is indistinguishable from "still
broken" and wastes a debugging round.

## Reloading the add-on while iterating

`F3` → "Reload Scripts" and toggling the add-on off/on both only re-run
`register()`/`unregister()` — neither forces Python to re-import already-
cached submodules, which is unreliable for a multi-file package like this
one. Use the force-reload snippet in `docs/TESTING.md` §2 (purges
`sys.modules` before re-enabling) when a change isn't taking effect and F3
doesn't explain why.

## Keeping docs in sync

Whenever a change affects user-visible behavior, update the same turn, not
later:

- Behavior/install/usage changed → `README.md` and/or `docs/TESTING.md`
- New/changed CLI flag → `docs/CLI.md`
- Layering/module structure changed → `docs/ARCHITECTURE.md` and the
  PlantUML diagrams under `docs/architecture/`
- A step completed or newly discovered → `PLAN.md`

Stale docs are worse than no docs — don't leave one describing behavior
that no longer exists.

**This has already been missed once** — the click-to-add redesign (see
`docs/BUGS.md` #19) changed what `infrastructure/blender_mesh.py` does
(added viewport raycasting) and what `ui/properties.py` depends on (a
direct call into `operators/`, not just a `bl_idname`) across several
edits, and `docs/ARCHITECTURE.md`/`docs/architecture/*.puml` were left
describing the old design until the user explicitly asked "is the arch
docs updated?" — they weren't, and should have been updated in the same
turn as the code. So: **before treating any change to a file under
`infrastructure/`, `operators/`, or `ui/` as finished, explicitly check
whether the sentence in `docs/ARCHITECTURE.md` describing that
module still matches what the code does now** — don't wait to be asked.

## Git

Never create commits unless the user explicitly asks in that message.
Leave changes staged/unstaged for the user to review. When a task is
otherwise complete, say so and let the user decide when to commit — don't
commit "to wrap up."
