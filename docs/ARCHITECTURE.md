# Architecture

Polovoxel is a small, single-purpose Blender add-on: it lets an artist stamp
voxel cubes into a scene (first voxel, extrude-from-face, click-to-add, and a
cuboid grid stamp), backed by one panel and two keyboard shortcuts. The goal
of this document is to describe a **minimal** clean architecture for it —
enough structure to make the code testable and easy to navigate, without
turning a hobby add-on into an enterprise application.

## Package layout

```
polovoxel/
├── __init__.py                    # bl_info + register()/unregister() — composition root
├── domain/
│   └── geometry.py                # pure functions, zero bpy imports
├── infrastructure/
│   └── blender_mesh.py            # all bpy/bmesh-dependent adapters
├── operators/
│   ├── add_first_voxel.py         # one bpy.types.Operator per file
│   ├── add_voxel_on_face.py
│   ├── add_voxel_on_click.py
│   └── add_cuboid.py
├── ui/
│   ├── properties.py              # PropertyGroup (scene state)
│   └── panel.py                   # Panel (draws the UI)
└── keymaps.py                     # centralizes keymap registration
```

This mirrors the current single-file `polovoxel.py` almost 1:1 — nothing in
it is invented complexity, it is the same functions and classes moved into
files that describe what they are.

## The dependency rule

Clean architecture, at any scale, boils down to one rule: **dependencies
point inward, never outward.**

```
      ui/  operators/  infrastructure/  keymaps.py
        \        |          /
         v       v         v
              domain/
```

- **`domain/`** is the innermost layer. It has **zero `bpy`/`bmesh`
  imports** and zero Blender side effects. It only computes things:
  material names from an RGBA color, the target location for a new voxel
  given a face center/normal/scale, the list of grid coordinates for a
  cuboid stamp. Because it touches no Blender API, it can be imported and
  unit-tested with plain `python -m pytest`, outside Blender entirely —
  something impossible for the rest of the add-on.
- **`infrastructure/`** depends on `domain/` (for coordinates and material
  names) but never the reverse. It is where every `bpy.ops`, `bpy.data`,
  and `bmesh` call lives: creating the actual cube object, assigning
  materials, reading the selected face out of the edit-mesh `bmesh`.
- **`operators/`** depend on `domain/` and `infrastructure/` to implement
  one user-facing action each (`Add first voxel`, `Add voxel on face`, `Add
  voxel on click`, `Add cuboid`). An operator's `execute`/`modal`/`invoke`
  reads properties, asks `domain/` to compute a location, and asks
  `infrastructure/` to realize it in the scene. Operators never talk to
  each other directly.
- **`ui/`** (`properties.py`, `panel.py`) depends on `operators/` bl_idnames
  and on `domain/` only incidentally (e.g. default color). The panel just
  draws widgets and invokes operators by name — it holds no business logic.
- **`keymaps.py`** depends on the operator bl_idnames it wires shortcuts to.
  It is pulled out on its own because keymap registration/unregistration is
  a distinct lifecycle concern (and the current code has bugs here — see
  below) that deserves one obvious place to look, instead of being
  scattered across each operator class.
- **`__init__.py`** is the composition root: it imports the classes from
  every other module, registers/unregisters them with Blender, and calls
  into `keymaps.register()`/`keymaps.unregister()`. It contains no logic of
  its own beyond wiring — if you deleted every other file's contents this
  file would still tell you what the add-on is made of.

The rule in one sentence: **`domain/` knows nothing about Blender; every
other layer knows about Blender but only `infrastructure/` is allowed to
call `bpy`/`bmesh` to touch mesh data.** `operators/`, `ui/`, and
`keymaps.py` are all allowed to call `bpy` too (Blender's API forces
operators and panels to be `bpy.types` subclasses), but the *mesh-editing*
bpy calls — `primitive_cube_add`, material assignment, walking the
`bmesh` face list — are consolidated in `infrastructure/blender_mesh.py`
alone, so there is exactly one place to look when something about how a
cube gets created needs to change.

## Bugs this layout fixes along the way

Splitting `keymaps.py` out surfaces (and fixes) three bugs present in the
current `polovoxel.py`:

1. `PolovoxelAddFirstVoxelOperator.key_map` and
   `PolovoxelAddCuboidVoxelOperator.key_map` are defined as `def
   key_map(self)` and call `self.keymap_items.new(...)`, but `self` here is
   an *operator instance*, not the `km` keymap passed in at the call site
   for `PolovoxelAddVoxelOperator.key_map(km)`. Only the latter is actually
   a valid keymap-adding call.
2. `PolovoxelAddCuboidVoxelOperator.key_map` registers
   `PolovoxelAddFirstVoxelOperator.bl_idname` instead of its own — copy-paste
   bug, so Ctrl+Alt+C would never do what its label promises even if bug 1
   were fixed.
3. `register()` assigns `bpy.types.Scene.polovoxel_properties` but
   `unregister()` deletes `bpy.types.Object.polovoxel_properties` — a
   different type entirely, so unregistering an add-on that was properly
   registered raises `AttributeError` instead of cleaning up.

`keymaps.py` gives keymap add/remove exactly one function each
(`register(addon_keymaps)` / `unregister(addon_keymaps)`), built from each
operator's real `bl_idname`, so there is one obvious, testable place these
bugs live and get fixed instead of three near-duplicate `key_map` methods
scattered across operator classes.

## Why this counts as "clean architecture" at this scale

Robert C. Martin's original clean/hexagonal architecture is about large
systems with many use cases, multiple delivery mechanisms, and swappable
frameworks. Polovoxel has none of that: it has one delivery mechanism
(Blender), four use cases, and a UI that is just four widgets. Applying the
full-weight version (use-case interactors, gateways, DTOs, dependency
injection containers) would be over-engineering for ~600 lines of code.

What we keep from clean architecture, because it earns its keep even here,
is just the one rule that matters: **isolate the parts of the code that
have no reason to know about the framework.** Concretely:

- Moving grid math and material-name formatting into `domain/` means those
  functions can be unit-tested with plain `pytest`, without a running
  Blender process — which is otherwise impossible for *anything* in this
  add-on today, since `polovoxel.py` imports `bpy` at the top of the file.
- Splitting `infrastructure/` from `operators/` means changing *how* a cube
  is created (say, using `bmesh.ops` instead of `bpy.ops.mesh.primitive_
  cube_add`) touches one file, not four operator classes.
- One operator per file makes each use case independently readable —
  `add_cuboid.py` never has to be scrolled past to review
  `add_first_voxel.py`.
- `keymaps.py` gives keymap bugs (see above) one place to be fixed and one
  place to be reviewed, instead of being duplicated per-operator.

Everything else about the add-on — a flat four-layer package, no
interfaces/protocols, no dependency-injection framework, direct imports
instead of a registry — stays as simple as the single-file version. The
architecture is "clean" only in the narrow, load-bearing sense: **domain
logic is separated from framework side effects, and dependencies point one
way.** That is the smallest version of clean architecture that still gives
this add-on unit-testable core logic and a maintainable place to add a
fifth operator later.
