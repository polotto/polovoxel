"""Application layer: one use case per user-facing action.

Each use case orchestrates `domain/` math against its injected
`domain.mesh_repository.MeshRepository` to implement one thing the user
can do — add a voxel, add a cuboid, etc. A use case module never imports
`infrastructure/` directly; `operators/` call these instead of reaching
into `domain/`/`infrastructure/` themselves. See `factory.py` for the one
place that constructs the concrete `BlenderMeshRepository` and wires it in.
"""
