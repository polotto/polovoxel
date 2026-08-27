# Polovoxel — Bug & Code-Smell Audit

**File audited:** `polovoxel.py` (627 lines)
**Date:** 2026-08-19
**Method:** full manual read-through of the source, cross-checked against repo contents (`Polovoxel_0.0.2.zip`, `bl_info`).

Severity scale: **High** = crash, silent data corruption, or a stated feature that never works. **Medium** = wrong behavior in common paths, but with a workaround or narrow trigger. **Low** = code smell, maintainability risk, or cosmetic/metadata issue with no functional crash.

---

## Findings

### 1. `unregister()` deletes the property from the wrong type — leaves a dangling `Scene` attribute and can crash on add-on disable
- **Location:** `register()` line 594 vs `unregister()` line 612.
- **Severity:** High
- **Evidence:**
  ```python
  # register() — line 594
  bpy.types.Scene.polovoxel_properties = bpy.props.PointerProperty(type=PolovoxelPanelProperties)

  # unregister() — line 612
  del bpy.types.Object.polovoxel_properties
  ```
- **Failure scenario:** Disabling or uninstalling the add-on runs `unregister()`, which tries `del bpy.types.Object.polovoxel_properties` — an attribute that was never set (only `bpy.types.Scene.polovoxel_properties` was). This raises `AttributeError: type object 'Object' has no attribute 'polovoxel_properties'`, so unregister fails, the real `Scene.polovoxel_properties` (and the panel/property classes, whose `unregister_class` calls happen *before* this line but the keymap cleanup happens *after* it) is left dangling, and Blender logs a traceback every time the user disables the add-on.
- **Fix:** Change the delete target to match what was set, and do it defensively:
  ```python
  if hasattr(bpy.types.Scene, "polovoxel_properties"):
      del bpy.types.Scene.polovoxel_properties
  ```

### 2. `PolovoxelAddCuboidVoxelOperator.key_map` binds the wrong operator's `bl_idname`, and the method is never invoked at all
- **Location:** `PolovoxelAddCuboidVoxelOperator.key_map`, lines 220–222; `register()`, lines 604–605.
- **Severity:** Medium
- **Evidence:**
  ```python
  class PolovoxelAddCuboidVoxelOperator(bpy.types.Operator):
      ...
      def key_map(self):
          return self.keymap_items.new(PolovoxelAddFirstVoxelOperator.bl_idname, type='C', value='PRESS', ctrl=True, alt=True)
  ```
  and in `register()` only two keymaps are ever added:
  ```python
  addon_keymaps.append((km, PolovoxelAddVoxelOperator.key_map(km)))
  addon_keymaps.append((km, PolovoxelAddFirstVoxelOperator.key_map(km)))
  ```
- **Failure scenario:** The operator's own `bl_label` advertises "Create voxel cuboid (Ctrl + Alt + C)", but (a) `register()` never calls `PolovoxelAddCuboidVoxelOperator.key_map(...)` so `Ctrl+Alt+C` is never bound to anything, and (b) even if it were called, it would bind `Ctrl+Alt+C` to `PolovoxelAddFirstVoxelOperator`'s `bl_idname` (add-single-voxel-at-origin) instead of the cuboid operator — colliding with intent and silently doing the wrong thing.
- **Fix:** Correct the idname and actually register the keymap:
  ```python
  def key_map(self):
      return self.keymap_items.new(PolovoxelAddCuboidVoxelOperator.bl_idname, type='C', value='PRESS', ctrl=True, alt=True)
  ```
  and in `register()`:
  ```python
  addon_keymaps.append((km, PolovoxelAddCuboidVoxelOperator.key_map(km)))
  ```

### 3. Panel overwrites `width` with `height`, so the cuboid's height field from the UI is never applied
- **Location:** `PolovoxelPanel.draw`, lines 557–558.
- **Severity:** High
- **Evidence:**
  ```python
  props.width = world.polovoxel_width
  props.width = world.polovoxel_height   # <-- should be props.height
  props.depth = world.polovoxel_depth
  ```
- **Failure scenario:** A user sets Width=5 and Height=3 in the panel. `props.width` is set to 5, then immediately clobbered to 3 (the height value); `props.height` is never assigned at all, so it silently keeps its operator-default value of `2`. Every cuboid the user draws from the panel therefore ignores the UI's Height field and uses width = the height value instead of the width value — a plainly wrong result for the panel's headline feature.
- **Fix:**
  ```python
  props.width = world.polovoxel_width
  props.height = world.polovoxel_height
  props.depth = world.polovoxel_depth
  ```

### 4. `voxel_size = 2 * int(math.ceil(self.scale))` is lossy for non-integer scale and crashes at `scale == 0`
- **Location:** `PolovoxelAddCuboidVoxelOperator.main`, line 286.
- **Severity:** High
- **Evidence:**
  ```python
  voxel_size = 2 * int(math.ceil(self.scale))
  location_x_range = range(self.x_location, self.x_location + (self.width * voxel_size), voxel_size)
  ```
  `self.scale` is a `FloatProperty` with `min=0.0` and no upper bound, so any value (including `0.0` or `1.3`) is legal input.
- **Failure scenario:**
  - `scale = 0.0` (allowed by `min=0.0`, and is the property's floor) → `math.ceil(0.0) = 0` → `voxel_size = 0` → `range(x, x+..., 0)` raises `ValueError: range() arg 3 must not be zero`, crashing the operator.
  - `scale = 1.3` → actual cube edge length is `2 * 1.3 = 2.6`, but `voxel_size` rounds up to `2 * 2 = 4`, so voxels are spaced 4 units apart while only 2.6 units wide — leaving visible gaps between voxels in the cuboid grid. Non-integer, non-half-integer scales are effectively unusable for the cuboid tool.
- **Fix:** Compute spacing from the actual cube size instead of an integer ceiling, and switch the loops to float-safe iteration (or keep `range` but validate `scale > 0` first):
  ```python
  if self.scale <= 0:
      self.report({'WARNING'}, "Scale must be greater than 0")
      return
  voxel_size = 2 * self.scale
  # then build coordinates with a manual float stepping loop, e.g.
  xs = [self.x_location + i * voxel_size for i in range(self.width)]
  ```

### 5. Modal click operator dereferences `context.active_object.mode` with no `None` guard
- **Location:** `PolovoxelAddOnClickVoxelOperator.modal`, line 338.
- **Severity:** High
- **Evidence:**
  ```python
  if event.value != 'CLICK' or (not self.enable_with_click) or context.active_object.mode != 'EDIT':
      return {'PASS_THROUGH'}
  ```
- **Failure scenario:** The operator is started via `invoke()` (which only checks `context.object`, not `context.active_object`, and does not keep that object selected/active for the operator's lifetime). If the user then clicks somewhere with no active object (e.g. after deleting the object, or clicking empty viewport space that deselects everything) while "Enable add with click" is on, `context.active_object` is `None` and `None.mode` raises `AttributeError: 'NoneType' object has no attribute 'mode'`, crashing the modal operator with a Python traceback in Blender's console.
- **Fix:**
  ```python
  active = context.active_object
  if event.value != 'CLICK' or (not self.enable_with_click) or active is None or active.mode != 'EDIT':
      return {'PASS_THROUGH'}
  ```

### 6. Inconsistent, fragile `key_map` method signatures across operators
- **Location:** `PolovoxelAddVoxelOperator.key_map`, line 129 (`def key_map(km):`, no `self`/`@staticmethod`) vs. `PolovoxelAddFirstVoxelOperator.key_map` / `PolovoxelAddCuboidVoxelOperator.key_map`, lines 178 and 220 (`def key_map(self):`).
- **Severity:** Medium
- **Evidence / why it "works":**
  ```python
  def key_map(km):                     # looks like an instance method but isn't
      return km.keymap_items.new(...)
  ...
  addon_keymaps.append((km, PolovoxelAddVoxelOperator.key_map(km)))          # km passed as "km" — fine
  addon_keymaps.append((km, PolovoxelAddFirstVoxelOperator.key_map(km)))     # km passed as "self" — only works because km happens to expose .keymap_items too
  ```
  Both call sites call the function *unbound* on the class (`ClassName.key_map(km)`), so the first parameter receives the `KeyMap` object regardless of whether it's named `km` or `self`. It currently "works" for `PolovoxelAddFirstVoxelOperator` purely by coincidence — `self.keymap_items.new(...)` resolves correctly only because the caller happened to pass in a real `KeyMap` object where `self` was expected, not because the code is calling it as a bound instance method the way `self`-named methods normally imply.
- **Failure scenario:** A future maintainer, seeing `def key_map(self):`, reasonably assumes it must be called as `instance.key_map()` or decorated `@staticmethod`/`@classmethod`. Calling it that way (e.g. `op_instance.key_map()`) passes the operator instance as `self`, and `self.keymap_items` does not exist on an `Operator` instance → `AttributeError`. The inconsistency makes the two nearly-identical methods behave differently depending on how they're invoked, which is a maintenance trap.
- **Fix:** Make all three consistent — e.g. `@staticmethod def key_map(km): return km.keymap_items.new(...)` on every operator class, and call them uniformly as `PolovoxelXOperator.key_map(km)`.

### 7. Dead, commented-out code left in multiple places
- **Location:** lines 331–333, 341–344, 365–369 (`PolovoxelAddOnClickVoxelOperator.modal`), lines 392–408 (`PolovoxelPanelProperties`, a commented-out alternate implementation that would have added `polovoxel_scale`/`polovoxel_color` onto `bpy.types.Object`/`bpy.types.Scene` directly — notably this abandoned draft is what finding #1's `unregister()` code still assumes exists), and lines 625–626 (`# bpy.ops.object.polovoxel_operator()`).
- **Severity:** Low
- **Failure scenario:** No runtime failure, but the debug `print(...)` comments and the abandoned property-registration draft add noise, obscure the actual data model in use, and (as seen in finding #1) leave stale assumptions in the codebase that cause real bugs when only half-updated.
- **Fix:** Delete dead/commented code; if it documents a deliberate design alternative, capture that as a short note in `README.md`/`PLAN.md` instead of inline comments.

### 8. `bl_info["version"]` is out of sync with the shipped release artifact
- **Location:** `bl_info["version"]`, line 11; repository file `Polovoxel_0.0.2.zip`.
- **Severity:** Low
- **Evidence:** `bl_info` declares `"version": (0, 0, 3)` but the only packaged release checked into the repo is `Polovoxel_0.0.2.zip`.
- **Failure scenario:** A user downloading `Polovoxel_0.0.2.zip` from the repo and checking Blender's add-on preferences (which reads `bl_info["version"]`) sees "0.0.3", creating confusion about what version they actually installed and making bug reports/version-based troubleshooting unreliable.
- **Fix:** Either bump the packaged zip to `Polovoxel_0.0.3.zip` (regenerated from current source) as part of the release process, or roll `bl_info["version"]` back to `(0, 0, 2)` until a new zip is actually cut. Consider automating zip naming from `bl_info["version"]` to prevent future drift.

### 9. Duplicated "compute cube location above the selected face" logic between two operators
- **Location:** `PolovoxelAddVoxelOperator.main`, lines 159–170, and `PolovoxelAddOnClickVoxelOperator.modal`, lines 346–357.
- **Severity:** Low
- **Evidence:** Both blocks independently do:
  ```python
  selected_center_location, selected_normal = get_first_selected_face_center_location(context)
  if selected_center_location:
      cube_scale = (self.scale, self.scale, self.scale)
      cube_location = selected_center_location + (selected_normal * Vector(cube_scale))
      mat_name = get_material_name(self.color)
      cube_color = self.color
      create_cube(context, cube_location, cube_scale, mat_name, cube_color)
  ```
- **Failure scenario:** Any fix or behavior change to "place a new voxel adjacent to the selected face" (e.g. finding-4-style scale handling, or adding an offset option) must be made in two places; it's easy to update one call site and forget the other, causing the click-to-add and menu-add-voxel features to silently diverge.
- **Fix:** Extract a shared helper, e.g. `add_voxel_on_selected_face(context, scale, color)`, and call it from both `PolovoxelAddVoxelOperator.main` and `PolovoxelAddOnClickVoxelOperator.modal`.

### 10. Bare `except:` clauses swallow all errors, including unrelated ones
- **Location:** `setup_obj_material`, lines 72–75; `create_cube`, lines 79–82 and 87–90.
- **Severity:** Low
- **Evidence:**
  ```python
  try:
      bpy.context.space_data.shading.type = 'MATERIAL'
  except:
      pass
  ```
- **Failure scenario:** These bare `except:` blocks catch *every* exception (including `KeyboardInterrupt`/`SystemExit` and unrelated bugs like a typo'd attribute name elsewhere accidentally triggered in the same `try`), not just the specific "no 3D viewport space_data available" case they're meant to guard against. This makes real regressions in `mode_set`/`shading` handling invisible — they just silently no-op instead of surfacing.
- **Fix:** Catch the specific expected exception type, e.g. `except AttributeError:` / `except RuntimeError:`, and consider logging via `self.report()` at least in debug builds.

### 11. Leftover debug `print()` statement in the cuboid operator
- **Location:** `PolovoxelAddCuboidVoxelOperator.main`, line 291.
- **Severity:** Low
- **Evidence:** `print(location_x_range)` — prints a `range(...)` object (not even useful output) on every cuboid creation.
- **Failure scenario:** Spams Blender's system console on every use of "Create voxel cuboid," making real log/error output harder to spot; no functional impact but is release-quality debug residue.
- **Fix:** Remove the `print` call.

### 12. Dead statement: `CollectionProperty` created but never assigned
- **Location:** `register()`, line 596.
- **Severity:** Low
- **Evidence:**
  ```python
  props = bpy.props.CollectionProperty(type=PolovoxelPanelProperties)
  ```
  `props` is a local variable that is never read again in `register()` and never attached to any `bpy.types.*`.
- **Failure scenario:** No crash, but it's misleading dead code that looks like it should be registering something (a `CollectionProperty`, as opposed to the `PointerProperty` on the line above) and isn't — a maintainer could waste time trying to find where it's used, or assume collection-based multi-instance properties are supported when they aren't wired up at all.
- **Fix:** Delete the line, or if collection support was intended, actually assign it, e.g. `bpy.types.Scene.polovoxel_properties_collection = props`.

### 13. Misleading local-variable type annotation using `PointerProperty` at runtime
- **Location:** `create_cube`, line 92.
- **Severity:** Low
- **Evidence:**
  ```python
  cube_obj: PointerProperty(type=bpy.types.Object) = context.active_object
  ```
- **Failure scenario:** `bpy.props.PointerProperty(...)` is meant to be used as a class-body property definition (evaluated by Blender's RNA machinery when a class is registered), not as a PEP 526 variable annotation on an ordinary local variable inside a function body. Here, Python evaluates `PointerProperty(type=bpy.types.Object)` fresh on *every single call* to `create_cube` purely as a throwaway annotation object that is immediately discarded — wasted work and, more importantly, deeply confusing to any reader who assumes `cube_obj` is being declared as an actual Blender property (it is just a plain local variable holding `context.active_object`).
- **Fix:** Use a normal, un-annotated (or plainly-typed) assignment: `cube_obj = context.active_object` (optionally `cube_obj: bpy.types.Object = context.active_object` using the real class, not `PointerProperty`, purely for IDE hinting).

### 14. `execute()` on two operators calls `self.main(bpy.context)` instead of using the passed-in `context`
- **Location:** `PolovoxelAddFirstVoxelOperator.execute`, line 201; `PolovoxelAddCuboidVoxelOperator.execute`, line 281. Contrast with `PolovoxelAddVoxelOperator.execute`, line 149, which correctly passes through the `context` argument it received.
- **Severity:** Low
- **Evidence:**
  ```python
  def execute(self, context):
      ...
      self.main(bpy.context)     # ignores the `context` parameter entirely
  ```
- **Failure scenario:** `bpy.context` and the `context` passed into `execute()` are normally the same object, so this doesn't misbehave in ordinary UI-driven use — but operators are also commonly invoked programmatically with an *overridden* context (`bpy.ops.object.polovoxel_add_first_voxel_operator({'area': ...}, ...)`, common in automation/export scripts and testing), and in those cases `bpy.context` silently diverges from the intended `context`, causing the operator to act on the wrong window/area/active object. It's also just an inconsistency between otherwise-identical operator classes.
- **Fix:** Use the `context` parameter consistently: `self.main(context)`.

### 15. Panel is registered under the World properties tab, contradicting `bl_info["location"]`
- **Location:** `PolovoxelPanel.bl_context = "world"`, line 478, vs. `bl_info["location"] = "Object Properties > Polovoxel"`, line 13.
- **Severity:** Low
- **Evidence:** `bl_context = "world"` places the panel in the World properties tab (and the code even names the property accessor `world = context.scene.polovoxel_properties`, line 483), while `bl_info` tells users/the add-on browser it lives under Object Properties.
- **Failure scenario:** A user reads the add-on's own metadata ("Object Properties > Polovoxel"), goes to the Object properties tab, and doesn't find the panel — it's actually under World properties. Minor discoverability/documentation bug, not a crash.
- **Fix:** Either change `bl_context` to `"object"` to match the documented location, or update `bl_info["location"]` to say `"Properties > World > Polovoxel"` to match the actual implementation, and rename the local variable from `world` to something scene/property-group-neutral (e.g. `props_group`) to reduce confusion with finding #1's Scene-vs-Object mismatch.

### 16. Unused `invoke()` state on the click operator
- **Location:** `PolovoxelAddOnClickVoxelOperator.invoke`, lines 378–379.
- **Severity:** Low
- **Evidence:** `self.first_mouse_x = event.mouse_x` and `self.first_value = context.object.location.x` are set but never referenced anywhere else in the class (the leftover commented-out block at lines 365–369 is the only place that once used something similar).
- **Failure scenario:** No functional bug, but it's misleading — it looks like drag-based delta tracking was planned/removed, leaving unused state that suggests functionality that doesn't actually exist.
- **Fix:** Remove the two unused assignments, or if drag-delta behavior is planned, implement and use them.

### 17. Material color never applied to the node graph, so voxels render gray in Material Preview/Rendered shading
- **Location:** `setup_obj_material`, original `polovoxel.py` lines 56–75 (now `polovoxel/infrastructure/blender_mesh.py`, found post-refactor via live testing, 2026-08-26).
- **Severity:** High
- **Evidence:**
  ```python
  mat = bpy.data.materials.new(name=name)
  mat.diffuse_color = color        # only affects Solid shading's "Material" color mode
  ...
  bpy.context.space_data.shading.type = 'MATERIAL'   # forces Material Preview shading
  ```
- **Failure scenario:** `bpy.data.materials.new()` creates a node-based material by default in Blender 2.8+ (`use_nodes=True`, with a default Principled BSDF). `diffuse_color` only drives the legacy Solid-shading swatch — it is ignored by Material Preview/Rendered, which read the node graph instead. Since the Principled BSDF's Base Color was never set, every operator that adds a voxel also force-switches the viewport into Material Preview shading (`space_data.shading.type = 'MATERIAL'`), and the result is every voxel showing the node graph's default gray — the user's chosen color is invisible, and the sudden Material Preview switch (different background/lighting) reads as "the view changed and the colors disappeared."
- **Fix:** After creating the material, also set the Principled BSDF's Base Color:
  ```python
  if mat.use_nodes:
      bsdf = mat.node_tree.nodes.get('Principled BSDF')
      if bsdf is not None:
          bsdf.inputs['Base Color'].default_value = color
  ```
  Fixed in `polovoxel/infrastructure/blender_mesh.py`. The forced
  `space_data.shading.type = 'MATERIAL'` call was also removed entirely
  (2026-08-26) rather than kept as a "helpful" auto-switch: with
  `diffuse_color` and the Base Color both set correctly, the color is
  already right in whichever shading mode (Solid, Material Preview,
  Rendered) the user happens to be in, so forcibly changing their viewport
  shading on every voxel add was unwanted surprise behavior, not a
  necessary fix.

### 18. No operator declares `bl_options = {'REGISTER', 'UNDO'}` — fragmented undo steps can crash Blender on Cmd/Ctrl+Z
- **Location:** All four operator classes, original `polovoxel.py` (none ever set `bl_options`), now `polovoxel/operators/*.py` (found post-refactor via live testing — a real macOS crash report, 2026-08-26).
- **Severity:** High
- **Evidence:** `create_cube()` (`polovoxel/infrastructure/blender_mesh.py`) calls `bpy.ops.object.mode_set(mode='OBJECT')`, then `bpy.ops.mesh.primitive_cube_add(...)`, then `bpy.ops.object.mode_set(mode='EDIT')`, then assigns a material — several separate `bpy.ops` calls per voxel, invoked from operators that never declared `'UNDO'` in `bl_options`.
- **Failure scenario:** Without `'UNDO'`, Blender doesn't group everything an operator's `execute()`/`modal()` does into one atomic undo step; each nested `bpy.ops.object.mode_set`/`bpy.ops.mesh.primitive_cube_add` call pushes its own fragment onto the global undo stack instead. Repeated fast invocations — especially via the click-to-add modal operator, which can fire many times in quick succession — build a chain of undo steps that don't correspond to clean, self-consistent scene states. Pressing Cmd+Z (macOS) / Ctrl+Z later asks Blender's memfile undo system to decode one of these steps, which can dereference a dangling/partially-written ID reference and crash the whole application (`EXC_BAD_ACCESS`/`SIGSEGV` inside `BKE_lib_query_foreachid_process`/`scene_foreach_id` while `blo_read_file_internal` reads the memfile snapshot — not a Python-level exception, a native crash with no add-on traceback). This matches the exact "add-on breaks Blender undo" failure category linked in this project's own README resources.
- **Fix:** Add `bl_options = {'REGISTER', 'UNDO'}` to every `bpy.types.Operator` subclass so each user action (one voxel, one cuboid, one click-added voxel) is grouped into a single, well-formed undo step. Fixed on all four operators in `polovoxel/operators/`.

### 19. "Enable add with click" checkbox does nothing — the click-to-add modal operator is never invoked
- **Location:** Original `polovoxel.py`, `PolovoxelPanelProperties.polovoxel_enable_with_click` (no `update` callback) plus `PolovoxelAddOnClickVoxelOperator`, only ever invoked from `if __name__ == "__main__":` at the bottom of the file (lines 620–626, found post-refactor via live testing, 2026-08-26).
- **Severity:** High
- **Evidence:**
  ```python
  if __name__ == "__main__":
      register()
      bpy.ops.object.polovoxel_add_on_click_voxel_operator('INVOKE_DEFAULT')
  ```
- **Failure scenario:** The checkbox only sets a plain `BoolProperty` on the scene — it has no `update` callback, and nothing else in `register()`/the panel ever calls `bpy.ops.object.polovoxel_add_on_click_voxel_operator('INVOKE_DEFAULT')` to actually start the modal operator whose `modal()` method reads that property and listens for `LEFTMOUSE` clicks. The only place that ever invoked it was the `__main__` guard, which only executes when the file is run directly via Blender's Text Editor ("Run Script") — never when the add-on is installed and enabled the normal way through Preferences. So for anyone who installs Polovoxel like a real add-on (the only documented install path), ticking "Enable add with click" visibly checks the box and does nothing else; clicking faces never adds voxels.
- **Fix:** Give `polovoxel_enable_with_click` an `update` callback that starts the modal operator (guarded by a module-level flag so toggling on/off repeatedly can't stack duplicate handlers that would double-add voxels per click). Implemented in `polovoxel/ui/properties.py` (`_on_enable_with_click_toggled`) and `polovoxel/operators/add_voxel_on_click.py` (`start_if_not_running`, `_running` guard, `cancel()`).
- **Known remaining limitation:** if a `.blend` file is saved with the checkbox already checked, reopening it does not auto-resume the modal (property `update` callbacks don't fire just because a stored value loads) — toggle the checkbox off and back on once per session to (re)start it. Resuming automatically on file load would need a deferred call from `register()`/a load-post handler and was judged out of scope for this fix.
- **Follow-up (2026-08-26, live testing after the fix above):** two more issues surfaced once the modal actually started running for the first time ever:
  1. `modal()` had no `context.area.type == 'VIEW_3D'` guard, so it reacted to `LEFTMOUSE` clicks anywhere in the Blender window (any panel, any editor), not just the 3D viewport.
  2. Every "didn't add a voxel" path returned `{'PASS_THROUGH'}` silently with no `self.report()`, so a click that didn't work gave zero feedback — indistinguishable from "still broken."
  Both fixed in the same file.
- **Design change (2026-08-26):** the original mechanism reused `add_voxel_on_selected_face`, which places the new voxel using whatever face is *already selected* in the edit-mesh at the moment `modal()` sees the click (not the face under the cursor), and deselected everything after a successful add. That meant **one click never both selected a face and added to it** — you had to click once to select, click again to add, requiring Edit Mode the whole time. That didn't match the intended behavior ("click any face, a voxel is added above it, immediately"), so click-to-add was rewritten to raycast from the mouse cursor directly (`Scene.ray_cast`, see `get_face_under_mouse`/`add_voxel_at_mouse` in `polovoxel/infrastructure/blender_mesh.py`) instead of reading edit-mesh selection state. It now works in any mode (Object or Edit) and needs no pre-selected face — a single click on any face immediately adds a voxel above it.
- **Follow-up 2 (2026-08-26):** `start_if_not_running()` was calling `bpy.ops.object.polovoxel_add_on_click_voxel_operator('INVOKE_DEFAULT')` directly from the property's `update` callback. Starting a modal operator (`modal_handler_add`) from inside a property update callback runs in a context Blender treats as restricted, and can silently fail to actually attach the handler — no exception, no popup, the checkbox just looks enabled while nothing listens. Fixed by deferring the call one tick via `bpy.app.timers.register(...)`, the documented-safe pattern for this. Also added an `self.report({'INFO'}, ...)` on successful start and a try/except around the per-click raycast+create (an uncaught exception inside `modal()` silently removes the handler, which would look identical to "never started" from the user's side) — so a click-to-add failure is now always visible in Blender's status bar / System Console instead of failing silently.
- **Follow-up 3 (2026-08-26, confirmed via live System Console output):** with the modal confirmed running (the "click-to-add is on" message appeared), clicking a face still silently did nothing. Two dead ends were tried and ruled out with real debug output before finding the actual cause:
  1. Switching `event.value == 'CLICK'` to `event.value == 'PRESS'` — didn't help, still silent.
  2. A temporary debug print on every `LEFTMOUSE` event revealed the real problem: `context.area`, `context.region`, and `context.region_data` were **all `None`** for every single event this modal received — `'CLICK'` values *were* arriving fine, so the earlier `'CLICK'` vs `'PRESS'` theory was a red herring. The `in_viewport = context.area is not None and ...` guard was unconditionally failing, silently discarding every click before it ever reached the raycast.
  Root cause: the operator is started via `bpy.app.timers` (the fix for Follow-up 2's context-restriction issue), and Blender does not populate per-event `context.area`/`context.region` for a modal handler that was attached from a timer callback the way it does for one invoked from a normal UI event — those two fixes were each individually correct and each exposed the next layer of the same underlying problem.
- **Fix:** stopped depending on `context.area`/`context.region`/`context.region_data` entirely. `get_face_under_mouse` now resolves the 3D viewport region itself: it scans `context.window.screen.areas` for a `VIEW_3D` area whose bounds contain the event's absolute window-space mouse position (`event.mouse_x`/`event.mouse_y`), then that area's `WINDOW`-type region the same way, and reads `region_3d` off `area.spaces.active` directly (`_find_view3d_region_under_mouse` in `polovoxel/infrastructure/blender_mesh.py`). The now-unreliable `context.area` check was removed from `modal()`.
- **Follow-up 4 (2026-08-26):** once clicks were finally adding voxels, they weren't flush against the clicked face — new cubes were offset by a few units and overlapping instead of sitting cleanly adjacent. Cause: `get_face_under_mouse` returned the *raw ray-hit point* (`location` from `Scene.ray_cast`), which lands wherever the cursor literally was on the face, not its center — offsetting a voxel from an arbitrary point-on-face instead of the face's center breaks the grid alignment every other placement path relies on. Fixed by using the hit face's actual center instead: `Scene.ray_cast` also returns a polygon `index` and the hit object's world `matrix`, so the center is computed as `matrix @ hit_obj.data.polygons[index].center` (local-space polygon center transformed to world space) rather than the raw hit point.

---

## Summary Table

| # | Title | Location | Severity |
|---|-------|----------|----------|
| 1 | `unregister()` deletes property from `Object` instead of `Scene` | `unregister()` L612 vs `register()` L594 | High |
| 2 | Cuboid `key_map` uses wrong `bl_idname` and is never called | L220-222, L604-605 | Medium |
| 3 | Panel overwrites `props.width` with height, height never applied | `PolovoxelPanel.draw` L557-558 | High |
| 4 | `voxel_size` via `math.ceil` is lossy / crashes at `scale=0` | `PolovoxelAddCuboidVoxelOperator.main` L286 | High |
| 5 | `context.active_object.mode` dereferenced without `None` check | `PolovoxelAddOnClickVoxelOperator.modal` L338 | High |
| 6 | Inconsistent `key_map` signatures (`km` vs `self`, no `@staticmethod`) | L129, L178, L220 | Medium |
| 7 | Dead commented-out code blocks | L331-333, 341-344, 365-369, 392-408, 625-626 | Low |
| 8 | `bl_info` version (0.0.3) out of sync with shipped zip (0.0.2) | L11 vs `Polovoxel_0.0.2.zip` | Low |
| 9 | Duplicated "place voxel on selected face" logic | L159-170 vs L346-357 | Low |
| 10 | Bare `except:` clauses hide unrelated errors | L74-75, 81-82, 89-90 | Low |
| 11 | Leftover debug `print()` | `PolovoxelAddCuboidVoxelOperator.main` L291 | Low |
| 12 | Dead `CollectionProperty(...)` statement, never assigned | `register()` L596 | Low |
| 13 | `PointerProperty` misused as a local variable type annotation | `create_cube` L92 | Low |
| 14 | `execute()` uses `bpy.context` instead of passed-in `context` | L201, L281 | Low |
| 15 | Panel `bl_context = "world"` contradicts documented Object-panel location | L478 vs L13 | Low |
| 16 | Unused mouse/location state set in `invoke()` | L378-379 | Low |
| 17 | Material color never set on the node graph — voxels render gray in Material Preview/Rendered | `setup_obj_material` | High |
| 18 | No operator declares `bl_options = {'REGISTER', 'UNDO'}` — fragmented undo can crash Blender on undo | All 4 operator classes | High |
| 19 | "Enable add with click" checkbox never starts the click-to-add modal operator | `PolovoxelPanelProperties`, `PolovoxelAddOnClickVoxelOperator` | High |
