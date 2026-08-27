# Testing Polovoxel

Practical guide for testing the `polovoxel/` add-on package locally while
iterating on it. Written for the author, not an end user — assumes you can
already read the source in this repo.

- Package under test: `polovoxel/`
- Manual smoke-test scene: `test.blend`
- Blender version: 2.80+ (`bl_info["blender"] = (2, 80, 0)`)

---

## 1. Install from source

Pick (a) for a "does it install like a real user's copy" check, or (b) for
fast iteration. Use (b) day-to-day.

### (a) Zip + Install (matches what a real user does)

```bash
cd /Users/angelopolotto/GitHub/polovoxel
zip -r polovoxel-dev.zip polovoxel
```

In Blender: **Edit > Preferences > Add-ons > Install...** → select
`polovoxel-dev.zip` → **Install Add-on** → enable the **Polovoxel** checkbox.

This copies the code into Blender's addons folder, so it does **not** pick
up further edits to your working copy — re-zip and re-install every time you
change something. Good for a final pre-release check, bad for iteration.

### (b) Symlink into Blender's addons folder (fast iteration)

Symlink `polovoxel/` straight into Blender's user addons directory so edits
in this repo are picked up immediately (after a reload, see §2):

```bash
# macOS, Blender 4.x example — adjust the version number to match your install.
# The addons/ folder usually doesn't exist until an add-on has been installed
# through it before, so create it first or the symlink will fail with
# "No such file or directory".
mkdir -p "/Users/$(whoami)/Library/Application Support/Blender/5.2/scripts/addons"
ln -s /Users/angelopolotto/GitHub/polovoxel/polovoxel \
      "/Users/$(whoami)/Library/Application Support/Blender/5.2/scripts/addons/polovoxel"
```

Default per-OS addons paths (swap `<version>` for your Blender version, e.g.
`4.2`):

| OS | Path |
|---|---|
| macOS | `/Users/<you>/Library/Application Support/Blender/<version>/scripts/addons/` |
| Linux | `~/.config/blender/<version>/scripts/addons/` |
| Windows | `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\` |

If the `addons` folder doesn't exist yet, create it (`mkdir -p`) before the
`ln -s`, or the symlink command fails with "No such file or directory".

**If Blender was already running when you created the folder/symlink**, it
won't see the new add-on module — Blender adds script/addon directories to
Python's `sys.path` at startup, so a folder that didn't exist yet at launch
isn't picked up by **Reload Scripts (F3)** or by toggling the add-on
checkbox off/on. The Add-ons list may still *show* "Polovoxel" (that list is
just a directory scan) but enabling it fails with `Add-on not loaded:
"polovoxel", cause: No module named 'polovoxel'`. Fix: **fully quit and
relaunch Blender** so it re-scans script paths at startup, then enable the
add-on again. This is a one-time cost — once the folder exists at launch,
normal Reload Scripts iteration works fine.

Then in Blender: **Edit > Preferences > Add-ons**, search "Polovoxel", enable
the checkbox. From now on, edits to files under `polovoxel/` in this repo are
live in Blender after a reload (§2) — no re-zip, no re-copy.

---

## 2. Reload after code changes

- **Recommended — force reload (reliable for this multi-file package)**:
  F3 "Reload Scripts", and even toggling the add-on off/on, both only
  re-run `unregister()`/`register()` — neither forces Python to re-import
  submodules it has already cached in `sys.modules`. For a single-file
  add-on that's fine; for a package split across `polovoxel/operators/`,
  `polovoxel/infrastructure/`, etc., it means edits to a submodule can
  silently **not** take effect, because `polovoxel/__init__.py`'s
  `from .operators.add_voxel_on_click import ...` just re-fetches the
  stale cached module instead of re-reading the file. Paste this into the
  **Python Console** (Scripting workspace tab) instead — it purges every
  `polovoxel*` entry from `sys.modules` before re-enabling, guaranteeing a
  fresh re-import of every file:
  ```python
  import sys, bpy
  bpy.ops.preferences.addon_disable(module="polovoxel")
  for name in list(sys.modules):
      if name == "polovoxel" or name.startswith("polovoxel."):
          del sys.modules[name]
  bpy.ops.preferences.addon_enable(module="polovoxel")
  print("Polovoxel: force-reloaded")
  ```
  No Blender restart needed — this is safe to run repeatedly while
  iterating.
- **Fastest, but only reliably picks up changes to `polovoxel/__init__.py`
  itself**: hover the 3D viewport and press **F3**, type "Reload Scripts",
  press Enter.
- **Equivalent to F3 for staleness purposes**: **Edit > Preferences >
  Add-ons** → toggle the Polovoxel checkbox off, then on again. This
  re-runs `unregister()`/`register()` but not the module re-import either.
- **Caveat — modal state**: `PolovoxelAddOnClickVoxelOperator` is a running
  modal operator once invoked (click-to-add mode). Reload Scripts does not
  cleanly tear down an in-flight modal operator. If click-to-add starts
  behaving oddly after several reloads (input not passing through, phantom
  handlers), press **Esc**/right-click to cancel it first, and if it's still
  wedged, fully restart Blender.
- **Caveat — keymaps**: `keymaps.py` appends to a module-level
  `addon_keymaps` list. A clean disable → enable cycle clears and rebuilds
  it correctly; if you ever edit `keymaps.py` itself while the old keymap
  entries are still registered, prefer a full restart to be sure you're not
  looking at a stale keymap item.

---

## 3. Console access & calling operators directly

### Open the consoles

- **Python console** (interactive REPL): switch any editor area to it, or
  use the default **Scripting** workspace tab at the top of Blender, which
  includes a Python Console panel.
- **System console** (stdout/stderr, tracebacks, `print()` output):
  - **Windows**: **Window > Toggle System Console**.
  - **macOS/Linux**: there's no menu toggle — launch Blender from a
    terminal instead, so its stdout/stderr prints to that terminal window:
    ```bash
    /Applications/Blender.app/Contents/MacOS/Blender
    ```
    Keep that Terminal window visible while you work — every `print()`,
    warning, and Python traceback (including from `self.report()` and
    unhandled exceptions in operators) shows up there.

### Drive the add-on from the Python console

```python
import bpy

# Check the add-on's scene state (created in register(), see polovoxel/__init__.py)
bpy.context.scene.polovoxel_properties.polovoxel_scale
bpy.context.scene.polovoxel_properties.polovoxel_color[:]

# Call operators directly by bl_idname (see each file under polovoxel/operators/)
bpy.ops.object.polovoxel_add_first_voxel_operator()          # add_first_voxel.py
bpy.ops.object.polovoxel_add_voxel_operator()                 # add_voxel_on_face.py (needs a selected face in Edit Mode)
bpy.ops.object.polovoxel_add_on_click_voxel_operator('INVOKE_DEFAULT')  # add_voxel_on_click.py — modal, needs INVOKE_DEFAULT
bpy.ops.object.polovoxel_add_plane_voxel_operator(width=3, height=2, depth=3)  # add_cuboid.py

# Override defaults for a one-off call
bpy.ops.object.polovoxel_add_first_voxel_operator(scale=2.0, color=(1, 0, 0, 1))
```

Tip: operators that read `context.scene.polovoxel_properties` inside
`execute()` will overwrite whatever kwargs you pass with the panel's current
values — that's intentional (see each operator's `execute()`), so to test a
specific scale/color from the console either set
`bpy.context.scene.polovoxel_properties.polovoxel_scale = ...` first, or call
`.main(bpy.context)` directly on an instantiated operator if you need to
bypass that.

---

## 4. Manual smoke test with `test.blend`

1. Open `/Users/angelopolotto/GitHub/polovoxel/test.blend` in Blender (with
   the add-on already enabled, per §1).
2. Go to **Properties editor > World tab** (the sphere-ish icon) — the
   **Polovoxel** panel lives there (`bl_context = "world"` in
   `polovoxel/ui/panel.py`), not under Object or Tool properties.
3. Set a **Scale** and **Color** at the top of the panel.
4. Click **Add first voxel** → a cube appears at the world origin.
5. Select the new object, **Tab** into **Edit Mode**, select one face (Face
   select mode, click a face), then click **Add voxel above selected face**
   in the panel (or press **Ctrl+Alt+I**) → a new voxel extrudes off that
   face.
6. Press **Ctrl+Alt+N** anywhere in the 3D viewport → adds another "first
   voxel" at the origin without touching the panel.
7. In the panel's **3D shapes** section, set X/Y/Z Location and
   Width/Height/Depth, click **Create voxel cuboid** (or **Ctrl+Alt+C**) →
   a solid block of voxels is generated matching all three dimensions.
8. Toggle **Enable add with click** on (toggling it, not just seeing it
   already checked, is what actually starts the click-listener — see
   `docs/BUGS.md` #19). Left-click any face of any existing cube in the 3D
   viewport — a new voxel is added directly above that face immediately, no
   pre-selection needed, and it works in either Object or Edit Mode (a ray
   is cast from the cursor into the scene, see `docs/BUGS.md` #19's design
   change note). Clicking empty space (nothing under the cursor) does
   nothing, silently. Toggle it back off and confirm clicking no longer
   adds voxels. Right-click or Esc should not crash the click-modal.

---

## 5. Manual test checklist

- [ ] Add-on installs and the **Polovoxel** checkbox enables with no error
      in the System Console
- [ ] Panel appears under **Properties > World** (not Object/Scene/Tool)
- [ ] "Add first voxel" creates a single cube at the origin, using the
      panel's current Scale and Color
- [ ] "Add voxel above selected face" (button and **Ctrl+Alt+I**) extrudes a
      correctly-placed voxel adjacent to the selected face in Edit Mode
- [ ] **Ctrl+Alt+N** shortcut adds a first voxel from anywhere in the 3D
      viewport
- [ ] **Ctrl+Alt+C** shortcut triggers the cuboid operator (previously
      unbound — verify it now fires at all)
- [ ] Cuboid generator: **Height** field in the panel actually changes the
      generated block's height (previously silently ignored/clobbered by
      Width — see `docs/BUGS.md` #3)
- [ ] Cuboid generator: Width/Depth also apply correctly, and voxel spacing
      has no visible gaps for a non-default Scale (e.g. try Scale = 1.3)
- [ ] Cuboid generator: setting Scale to `0` shows a warning
      (`self.report`) instead of crashing (see `docs/BUGS.md` #4)
- [ ] "Enable add with click" toggle turns click-to-add on/off; clicking
      empty space or with nothing selected does not crash the operator
- [ ] Disabling the add-on (**Preferences > Add-ons** checkbox off) produces
      **no error** in the System Console (previously crashed trying to
      delete a nonexistent `Object.polovoxel_properties` — see
      `docs/BUGS.md` #1)
- [ ] Re-enabling after a disable restores the panel and both shortcuts
- [ ] Reload Scripts (F3) picks up a trivial code change (e.g. edit a
      `bl_label` string) without restarting Blender

---

## 6. Troubleshooting

- **Panel doesn't show up** — you're on the wrong properties tab/context.
  It's under **Properties editor > World tab** specifically
  (`bl_context = "world"`), not Object, Scene, or Tool.
- **"Operator not found" / `bpy.ops.object.polovoxel_...` raises
  `AttributeError`** — the add-on isn't enabled. Check **Edit >
  Preferences > Add-ons** and confirm the Polovoxel checkbox is ticked; a
  failed `register()` also leaves operators unregistered even if the
  checkbox looks ticked, so check the System Console too.
- **Syntax/import error after editing code, or Reload Scripts silently does
  nothing** — check the **System Console** (launch Blender from Terminal on
  macOS, see §3). Reload failures print a full Python traceback there, not
  in the 3D viewport.
- **Shortcut doesn't fire (e.g. Ctrl+Alt+C)** — confirm your cursor is over
  the **3D viewport** when pressing it; the keymap is registered against the
  `'3D View'` keymap (`polovoxel/keymaps.py`) and won't trigger from other
  editor areas.
- **Click-to-add stops responding after several script reloads** — likely
  stale modal operator state (see §2 caveat). Esc/right-click to cancel,
  and if it's still wedged, restart Blender.
- **`Add-on not loaded: "polovoxel", cause: No module named 'polovoxel'`**
  — the `scripts/addons/polovoxel` symlink was created *after* Blender was
  already running, so the folder isn't on `sys.path` for this session (see
  the callout in §1(b)). Fully quit and relaunch Blender, then enable the
  add-on again — Reload Scripts and toggling the checkbox do **not** fix
  this specific error, only a full restart does.
