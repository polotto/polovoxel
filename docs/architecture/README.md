# Architecture Diagrams

Two minimal PlantUML diagrams for the Polovoxel add-on's clean-architecture layout.
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

UI --> Operators : invokes (bl_idname)
Keymaps --> Operators : binds shortcut to

Operators --> Infra : calls
Operators --> Domain : calls

Infra --> Domain : calls

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
