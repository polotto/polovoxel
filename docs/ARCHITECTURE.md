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
│   ├── geometry.py                # pure functions, zero bpy imports
│   └── mesh_repository.py         # MeshRepository — abstract port, zero bpy imports
├── infrastructure/
│   └── blender_mesh.py            # BlenderMeshRepository — the port's only concrete impl
├── usecases/
│   ├── add_first_voxel.py         # one use-case class per user action
│   ├── add_voxel_on_face.py
│   ├── add_voxel_on_click.py
│   ├── add_cuboid.py
│   └── factory.py                 # UseCaseFactory — builds use cases, wires the
│                                   # concrete MeshRepository into them
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

This started as the current single-file `polovoxel.py` moved almost 1:1
into files that describe what they are; the `usecases/` layer was added
once `operators/` calling `infrastructure/` directly turned out to be a
real layering violation, and `domain/mesh_repository.py` was added right
after that once `usecases/` calling `infrastructure/` directly turned out
to be the same violation one layer down — neither is invented complexity
for its own sake (see below).

## The dependency rule

Clean architecture, at any scale, boils down to one rule: **dependencies
point inward, never outward.**

```
      ui/  operators/  keymaps.py
             |
             v
         usecases/  ← use-case classes depend only on domain/
          |      \
          v       \  factory.py is the one exception: it imports
      domain/      \  infrastructure/ to construct the concrete repo
          ^          v
          | implements
   infrastructure/
```

- **`domain/`** is the innermost layer. It has **zero `bpy`/`bmesh`
  imports** and zero Blender side effects, and it is now two things:
  - `geometry.py` — pure functions: material names from an RGBA color, the
    target location for a new voxel given a face center/normal/scale, the
    list of grid coordinates for a cuboid stamp.
  - `mesh_repository.py` — the `MeshRepository` port: an `abc.ABC` with
    three abstract methods (`create_cube`, `get_first_selected_face_center_location`,
    `get_face_under_mouse`) and no implementation. It exists so `usecases/`
    can depend on an *abstraction* of "however the scene's meshes get
    created/read", not on `infrastructure/` itself — the Dependency
    Inversion half of clean architecture.
  Because neither file touches a Blender API, both can be imported and
  unit-tested with plain `python -m pytest`, outside Blender entirely —
  something impossible for the rest of the add-on.
- **`infrastructure/blender_mesh.py`** holds `BlenderMeshRepository`, the
  only concrete implementation of `domain.mesh_repository.MeshRepository`.
  It is where every `bpy.ops`, `bpy.data`, `bmesh`, and viewport/window-
  introspection call lives, each as one narrow, single-purpose method:
  creating the actual cube object, assigning a material, reading the
  selected face out of the edit-mesh `bmesh` — and, for click-to-add,
  resolving which 3D viewport region is under the mouse and raycasting
  (`Scene.ray_cast` via `bpy_extras.view3d_utils`) to find the clicked face
  directly, with no edit-mesh selection involved. It depends on `domain/`
  only to import the `MeshRepository` ABC it implements — never
  `domain/geometry.py`'s math, and it never combines its own methods into
  a multi-step flow itself; that orchestration is `usecases/`' job.
- **`usecases/`** is the application layer, sitting between `operators/`
  and `domain/`. One class per user-facing action (`Add first voxel`, `Add
  voxel on face`, `Add voxel on click`, `Add cuboid`), each with an
  `execute(context, ...)` method that does the actual orchestration: ask
  `domain/geometry.py` for the math (a location, a material name), then
  ask its injected `MeshRepository` to realize it in the scene. A use
  case's dependency is declared as the abstract port
  (`__init__(self, mesh_repo: MeshRepository)`) and injected through the
  constructor — the use case's own module **never imports
  `infrastructure/`**, only `domain/`. `usecases/factory.py` is the single
  place that imports the concrete `BlenderMeshRepository` to build the
  real instance a use case gets injected with — see its docstring for why
  that one file is the exception. This is the layer that fixes what used
  to be a direct `operators/` → `infrastructure/` dependency, and then
  (once the same violation showed up one layer down) a direct `usecases/`
  → `infrastructure/` dependency: `domain/mesh_repository.py`'s port is
  what let `usecases/` stop importing `infrastructure/` at all.
- **`usecases/factory.py`** holds `UseCaseFactory`, a small factory class
  with one `build_*` method per use case, all sharing one
  `BlenderMeshRepository` instance built in `__init__`. Its whole job is
  separating *construction* (deciding a use case gets the concrete
  Blender-backed repository and wiring it in) from *use* (an operator
  calling `.execute(...)` on an already-built instance) — so an operator's
  `main()` never has to know which concrete `MeshRepository` a use case
  needs, only that `factory.build_add_cuboid()` returns something with an
  `.execute()` to call. A single module-level `factory = UseCaseFactory()`
  instance is exported and imported by every operator that needs it.
- **`operators/`** depend on `usecases/` (via `usecases/factory.py`) to
  implement one user-facing action each. An operator's
  `execute`/`modal`/`invoke` reads properties, builds the matching use case
  from `factory`, and calls `.execute(...)` on it — no direct `domain/` or
  `infrastructure/` imports. Operators never talk to each other directly.
- **`ui/`** (`properties.py`, `panel.py`) depends on `operators/` and on
  `domain/` only incidentally (e.g. default color). Mostly this is
  `panel.py` invoking operators by `bl_idname` — declarative, no business
  logic. One property is the exception: `polovoxel_enable_with_click`'s
  `update` callback in `properties.py` directly imports and calls
  `operators.add_voxel_on_click.start_if_not_running()`, because a
  checkbox toggling scene state can't, by itself, start the modal operator
  that listens for clicks — something has to. Still a `ui/` → `operators/`
  dependency (the same direction as everything else), just a Python-level
  call instead of a `bl_idname` lookup.
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

The rule in one sentence: **`domain/` knows nothing about Blender;
`infrastructure/` is the only layer allowed to call `bpy`/`bmesh` to touch
mesh data, and it never combines those calls into a multi-step flow itself;
`usecases/` orchestrates `domain/` math against the abstract
`MeshRepository` port, never `infrastructure/` directly; and
`operators/`/`ui/`/`keymaps.py` never import `infrastructure/` or
`domain/mesh_repository.py` at all — they go through `usecases/`.** Only
`usecases/factory.py` is allowed to import `infrastructure/`, because
something has to construct the concrete repository a use case gets
injected with. `operators/`, `ui/`, and `keymaps.py` are all allowed to
call `bpy` too (Blender's API forces operators and panels to be
`bpy.types` subclasses), but the *mesh-editing* bpy calls —
`primitive_cube_add`, material assignment, walking the `bmesh` face list —
are consolidated in `infrastructure/blender_mesh.py` alone, so there is
exactly one place to look when something about how a cube gets created
needs to change.

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

This layout also made several *further* bugs easy to isolate and fix once
this structure was in place and actually exercised live in Blender —
missing `bl_options = {'REGISTER', 'UNDO'}`, a material color never
reaching the node graph, and the click-to-add feature never having worked
at all. See `docs/BUGS.md` findings #17–19 for the full detail; the
raycast-based click-to-add redesign described in the dependency rule above
(`infrastructure/`, `ui/` bullets) is a direct result of #19.

## Why this counts as "clean architecture" at this scale

Robert C. Martin's original clean/hexagonal architecture is about large
systems with many use cases, multiple delivery mechanisms, and swappable
frameworks. Polovoxel has none of that: it has one delivery mechanism
(Blender), four use cases, and a UI that is just four widgets. Applying the
full-weight version (gateways, DTOs, a dependency-injection framework, a
plugin registry) would be over-engineering for ~700 lines of code, and this
add-on still doesn't have any of that.

What it does have, as of the `usecases/` layer and `domain/mesh_repository.py`,
is use-case interactors, a repository port, and constructor-based
dependency injection — normally the "full-weight" parts of clean
architecture. They earned a place here for a concrete reason, not a
hypothetical one, and it happened twice in a row: first `operators/`
importing `infrastructure/` directly was a real layering violation (every
operator skipped straight past `domain/` to call bpy-dependent code), and
the fix — inserting `usecases/` as the layer operators should have gone
through — surfaced the same violation one level down, since the new
`usecases/` classes were then the ones importing `infrastructure/`
directly. `domain/mesh_repository.py`'s `MeshRepository` ABC is the fix for
*that*: it gives `usecases/` something to depend on that isn't a concrete
Blender adapter, so only `usecases/factory.py` — the construction point —
ever imports `infrastructure/` at all. `UseCaseFactory` itself stays one
small class, not a registry or a DI container: there's no
runtime-configurable swapping, no plugin discovery. The port earns its
keep because it makes each use case's dependency explicit and (in
principle) testable in isolation with a fake `MeshRepository`, not because
anything in the add-on actually needs multiple implementations at runtime.

What we keep from clean architecture, because it earns its keep even here,
is the one rule that matters: **isolate the parts of the code that have no
reason to know about the framework.** Concretely:

- Moving grid math and material-name formatting into `domain/` means those
  functions can be unit-tested with plain `pytest`, without a running
  Blender process — which is otherwise impossible for *anything* in this
  add-on today, since `polovoxel.py` imports `bpy` at the top of the file.
- Splitting `infrastructure/` from `usecases/` (via the `MeshRepository`
  port) means changing *how* a cube is created (say, using `bmesh.ops`
  instead of `bpy.ops.mesh.primitive_cube_add`) touches one file, not four
  use-case classes, and none of those use-case classes have to change at
  all — they only know about the abstract method names.
- Splitting `usecases/` from `operators/` means an operator's `main()` is
  three lines — build the use case, call `.execute(...)` — with no domain
  math or bpy orchestration to read past to see what the button does.
- One operator per file (and one use-case class per file) makes each user
  action independently readable — `add_cuboid.py` never has to be scrolled
  past to review `add_first_voxel.py`, in either package.
- `keymaps.py` gives keymap bugs (see above) one place to be fixed and one
  place to be reviewed, instead of being duplicated per-operator.

Everything else about the add-on — one port, not a family of interfaces;
no DTOs; no registry; direct imports instead of a plugin system — stays as
simple as the single-file version. The architecture is "clean" only in the
narrow, load-bearing sense: **domain logic is separated from framework side
effects, dependencies point one way, and no layer reaches past the one
directly below it.** That is the smallest version of clean architecture
that still gives this add-on unit-testable core logic, a fifth use case
that can be added without touching `infrastructure/`, a way to swap how a
cube gets created without touching a single use-case class, and a
maintainable place to add a fifth operator later.
