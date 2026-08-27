# Architecture Diagrams

Three minimal PlantUML diagrams for the Polovoxel add-on's clean-architecture layout.
See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the full written rationale.

## Components

One box per layer/module: `domain/` has no `bpy` dependency, and every other
layer depends inward on it (never the reverse). `__init__.py` is the only
place that wires registration together.

```plantuml
@startuml components
title Polovoxel — Component Overview

skinparam componentStyle rectangle
skinparam linetype ortho

package "__init__.py\n(composition root)" as Root {
}

package "operators/" as Operators {
  [add_first_voxel]
  [add_voxel_on_face]
  [add_voxel_on_click]
  [add_cuboid]
}

package "ui/" as UI {
  [panel.py]
  [properties.py]
}

package "keymaps.py" as Keymaps {
}

package "infrastructure/" as Infra {
  [blender_mesh.py]
}

package "domain/" as Domain {
  [geometry.py]
}

note bottom of Domain
  Pure Python, no bpy/bmesh imports.
  Everything else depends inward on it.
end note

Root ..> Operators : registers
Root ..> UI : registers
Root ..> Keymaps : registers

UI --> Operators : invokes (bl_idname)\nor calls directly (click-to-add toggle)
Keymaps --> Operators : binds shortcut to

Operators --> Infra : calls
Operators --> Domain : calls

Infra --> Domain : calls

note bottom of Infra
  Also raycasts the 3D viewport
  (bpy_extras.view3d_utils + Scene.ray_cast)
  for click-to-add — not just bmesh.
end note

@enduml
```

## Sequence: "Add voxel above selected face"

The most illustrative flow: the panel button triggers an operator, which
asks infrastructure for the selected face, hands the raw numbers to domain
for the pure location math, then asks infrastructure again to actually
create the cube and material in Blender.

```plantuml
@startuml sequence_add_voxel
title "Add voxel above selected face" — happy path

actor User
participant "Panel\n(ui/panel.py)" as Panel
participant "PolovoxelAddVoxelOperator\n(operators/add_voxel_on_face.py)" as Operator
participant "blender_mesh\n(infrastructure/)" as Infra
participant "geometry\n(domain/)" as Domain

User -> Panel : click "Add voxel above selected face"
Panel -> Operator : execute(context)

Operator -> Infra : add_voxel_on_selected_face(context, scale, color)
Infra -> Infra : get_first_selected_face_center_location(context)
note right : reads selected face\nvia bmesh

Infra -> Domain : compute_face_voxel_location(center, normal, scale)
Domain --> Infra : new cube location

Infra -> Domain : get_material_name(color)
Domain --> Infra : material name

Infra -> Infra : create_cube(...)
note right : bpy.ops.mesh.primitive_cube_add\n+ assign/create material

Infra --> Operator : done
Operator --> Panel : {'FINISHED'}
@enduml
```

## Sequence: "Click-to-add"

Genuinely different from the button/shortcut flow above, and worth its own
diagram: enabling the checkbox has to *start* a modal operator (deferred via
`bpy.app.timers`, since starting one directly from a property `update`
callback runs in a restricted context), and each click then raycasts the
viewport directly — no edit-mesh face selection involved, unlike every other
operator.

```plantuml
@startuml sequence_click_to_add
title "Click-to-add" — enable, then place a voxel

actor User
participant "properties.py\n(ui/)" as Props
participant "add_voxel_on_click\n(operators/)" as Operator
participant "blender_mesh\n(infrastructure/)" as Infra
participant "geometry\n(domain/)" as Domain

== Enabling ==
User -> Props : check "Enable add with click"
Props -> Operator : start_if_not_running()
note right : deferred one tick via\nbpy.app.timers — starting a modal\ndirectly from a property update\ncallback runs in a restricted context
Operator -> Operator : invoke() -> modal_handler_add(self)
Operator --> User : report "click-to-add is on"

== Each click ==
User -> Operator : LEFTMOUSE / PRESS (modal())
Operator -> Infra : add_voxel_at_mouse(context, event, scale, color)

Infra -> Infra : _find_view3d_region_under_mouse(context, event)
note right : context.area/region are None here\n(started via a timer) — resolved by\nscanning window.screen.areas against\nevent.mouse_x/mouse_y instead

Infra -> Infra : Scene.ray_cast(...)
note right : hit face's polygon.center,\nnot the raw ray-hit point —\nkeeps voxels grid-flush

Infra -> Domain : compute_face_voxel_location(center, normal, scale)
Domain --> Infra : new cube location

Infra -> Infra : create_cube(...)
Infra --> Operator : True (voxel created)
Operator --> User : consumes the click (RUNNING_MODAL)
@enduml
```

## Viewing the diagrams

- **VS Code**: install the "PlantUML" extension (jebbs.plantuml), open a
  `.puml` file, and press `Alt+D` to preview.
- **Online**: paste the contents of a `.puml` file into
  [plantuml.com/plantuml](https://www.plantuml.com/plantuml/uml/).
- **CLI**: if you have the `plantuml` command or `plantuml.jar` installed,
  run `plantuml docs/architecture/*.puml` from the repo root to render PNGs
  next to the source files.
- **GitHub**: the fenced ```` ```plantuml ```` blocks above render inline on
  GitHub automatically — no local tooling needed to just read them here.
