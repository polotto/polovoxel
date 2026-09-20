# Architecture Diagrams

Three minimal PlantUML diagrams for the Polovoxel add-on's clean-architecture
layout: one class diagram plus two sequence diagrams for the two distinct
"add a voxel" flows. See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the
full written rationale.

## Class Diagram

The actual classes, not just packages: `MeshRepository` is an `abc.ABC`
port defined in `domain/`, `BlenderMeshRepository` (`infrastructure/`) is
its only implementation, each `usecases/` class depends on the abstract
`MeshRepository` (injected through its constructor) rather than the
concrete class, and `UseCaseFactory` is the one place that constructs
`BlenderMeshRepository` and wires it into a use case — the composition
point between the abstraction the use cases depend on and the concrete
adapter that actually implements it. `__init__.py` (not shown) is the only
place that wires operator/UI registration together.

```plantuml
@startuml class_diagram
title Polovoxel — Class Diagram

skinparam classAttributeIconSize 0
hide empty members

package "domain" {
  class geometry <<module>> {
    +get_material_name(color)
    +compute_face_voxel_location(center, normal, scale)
    +compute_cuboid_voxel_locations(x, y, z, width, height, depth, scale)
  }

  abstract class MeshRepository {
    +{abstract} create_cube(context, location, scale, mat_name, color)
    +{abstract} get_first_selected_face_center_location(context)
    +{abstract} get_face_under_mouse(context, event)
  }
}

package "infrastructure" {
  class BlenderMeshRepository {
    +create_cube(context, location, scale, mat_name, color)
    +get_first_selected_face_center_location(context)
    +get_face_under_mouse(context, event)
    -_setup_obj_material(cube_obj, name, color)
    -_find_view3d_region_under_mouse(context, event)
  }
}

BlenderMeshRepository .up.|> MeshRepository : implements

package "usecases" {
  class AddFirstVoxelUseCase {
    -mesh_repo: MeshRepository
    +execute(context, scale, color)
  }
  class AddVoxelOnFaceUseCase {
    -mesh_repo: MeshRepository
    +execute(context, scale, color)
  }
  class AddVoxelAtMouseUseCase {
    -mesh_repo: MeshRepository
    +execute(context, event, scale, color)
  }
  class AddCuboidUseCase {
    -mesh_repo: MeshRepository
    +execute(context, x, y, z, width, height, depth, scale, color)
  }
  class UseCaseFactory {
    -mesh_repo: BlenderMeshRepository
    +build_add_first_voxel()
    +build_add_voxel_on_face()
    +build_add_voxel_at_mouse()
    +build_add_cuboid()
  }
}

AddFirstVoxelUseCase o-right-> MeshRepository : mesh_repo\n(injected)
AddVoxelOnFaceUseCase o-right-> MeshRepository : mesh_repo\n(injected)
AddVoxelAtMouseUseCase o-right-> MeshRepository : mesh_repo\n(injected)
AddCuboidUseCase o-right-> MeshRepository : mesh_repo\n(injected)

AddFirstVoxelUseCase ..> geometry : uses
AddVoxelOnFaceUseCase ..> geometry : uses
AddVoxelAtMouseUseCase ..> geometry : uses
AddCuboidUseCase ..> geometry : uses

UseCaseFactory o-down-> BlenderMeshRepository : constructs\n(the one exception —\nusecases/ otherwise never\nimports infrastructure/)
UseCaseFactory ..> AddFirstVoxelUseCase : builds
UseCaseFactory ..> AddVoxelOnFaceUseCase : builds
UseCaseFactory ..> AddVoxelAtMouseUseCase : builds
UseCaseFactory ..> AddCuboidUseCase : builds

package "operators" {
  class PolovoxelAddFirstVoxelOperator
  class PolovoxelAddVoxelOperator
  class PolovoxelAddOnClickVoxelOperator
  class PolovoxelAddCuboidVoxelOperator
}

PolovoxelAddFirstVoxelOperator ..> UseCaseFactory : factory
PolovoxelAddVoxelOperator ..> UseCaseFactory : factory
PolovoxelAddOnClickVoxelOperator ..> UseCaseFactory : factory
PolovoxelAddCuboidVoxelOperator ..> UseCaseFactory : factory

note bottom of MeshRepository
  Pure Python (abc), zero bpy imports.
  usecases/ depends on this abstraction,
  never on BlenderMeshRepository directly.
end note

note bottom of UseCaseFactory
  Separates construction (wiring the
  concrete BlenderMeshRepository into a
  use case) from use (an operator calling
  .execute(...) on the built instance).
end note

@enduml
```

## Sequence: "Add voxel above selected face"

The most illustrative flow: the panel button triggers an operator, which
builds the matching use case from `usecases/factory.py` and calls
`.execute(...)` on it. The use case asks its injected `MeshRepository`
(concretely a `BlenderMeshRepository`, but the use case only knows the
abstract port) for the selected face, hands the raw numbers to domain for
the pure location math, then asks the repository again to actually create
the cube and material in Blender — the operator itself never talks to
`domain/` or `infrastructure/`, and the use case itself never imports
`infrastructure/` either.

```plantuml
@startuml sequence_add_voxel
title "Add voxel above selected face" — happy path

actor User
participant "Panel\n(ui/panel.py)" as Panel
participant "PolovoxelAddVoxelOperator\n(operators/add_voxel_on_face.py)" as Operator
participant "factory\n(usecases/factory.py)" as Factory
participant "AddVoxelOnFaceUseCase\n(usecases/)" as UseCase
participant "BlenderMeshRepository\n(infrastructure/, implements\ndomain.MeshRepository)" as Repo
participant "geometry\n(domain/)" as Domain

User -> Panel : click "Add voxel above selected face"
Panel -> Operator : execute(context)

Operator -> Factory : build_add_voxel_on_face()
note right : factory is the only place that\nimports infrastructure/ directly,\nto construct the concrete repo
Factory --> Operator : AddVoxelOnFaceUseCase(mesh_repo)

Operator -> UseCase : execute(context, scale, color)
note right : UseCase only knows mesh_repo\nas the abstract MeshRepository port

UseCase -> Repo : get_first_selected_face_center_location(context)
note right : reads selected face\nvia bmesh
Repo --> UseCase : center, normal

UseCase -> Domain : compute_face_voxel_location(center, normal, scale)
Domain --> UseCase : new cube location

UseCase -> Domain : get_material_name(color)
Domain --> UseCase : material name

UseCase -> Repo : create_cube(...)
note right : bpy.ops.mesh.primitive_cube_add\n+ assign/create material
Repo --> UseCase : done

UseCase --> Operator : True
Operator --> Panel : {'FINISHED'}
@enduml
```

## Sequence: "Click-to-add"

Genuinely different from the button/shortcut flow above, and worth its own
diagram: enabling the checkbox has to *start* a modal operator (deferred via
`bpy.app.timers`, since starting one directly from a property `update`
callback runs in a restricted context), and each click then raycasts the
viewport directly — no edit-mesh face selection involved, unlike every other
operator. As with the flow above, the operator only ever talks to the use
case built from `usecases/factory.py`, and the use case only ever talks to
its injected `MeshRepository` port — neither imports `infrastructure/` or
`domain/` beyond that.

```plantuml
@startuml sequence_click_to_add
title "Click-to-add" — enable, then place a voxel

actor User
participant "properties.py\n(ui/)" as Props
participant "add_voxel_on_click\n(operators/)" as Operator
participant "factory\n(usecases/factory.py)" as Factory
participant "AddVoxelAtMouseUseCase\n(usecases/)" as UseCase
participant "BlenderMeshRepository\n(infrastructure/, implements\ndomain.MeshRepository)" as Repo
participant "geometry\n(domain/)" as Domain

== Enabling ==
User -> Props : check "Enable add with click"
Props -> Operator : start_if_not_running()
note right : deferred one tick via\nbpy.app.timers — starting a modal\ndirectly from a property update\ncallback runs in a restricted context
Operator -> Operator : invoke() -> modal_handler_add(self)
Operator --> User : report "click-to-add is on"

== Each click ==
User -> Operator : LEFTMOUSE / PRESS (modal())
Operator -> Factory : build_add_voxel_at_mouse()
note right : factory is the only place that\nimports infrastructure/ directly,\nto construct the concrete repo
Factory --> Operator : AddVoxelAtMouseUseCase(mesh_repo)

Operator -> UseCase : execute(context, event, scale, color)
note right : UseCase only knows mesh_repo\nas the abstract MeshRepository port

UseCase -> Repo : get_face_under_mouse(context, event)
Repo -> Repo : _find_view3d_region_under_mouse(context, event)
note right : context.area/region are None here\n(started via a timer) — resolved by\nscanning window.screen.areas against\nevent.mouse_x/mouse_y instead
Repo -> Repo : Scene.ray_cast(...)
note right : hit face's polygon.center,\nnot the raw ray-hit point —\nkeeps voxels grid-flush
Repo --> UseCase : face center, normal

UseCase -> Domain : compute_face_voxel_location(center, normal, scale)
Domain --> UseCase : new cube location

UseCase -> Repo : create_cube(...)
Repo --> UseCase : done

UseCase --> Operator : True (voxel created)
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
