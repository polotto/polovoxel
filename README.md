# Polovoxel

simple voxel add-on for blender

## Functions

- generate one cube/voxel on 0,0,0;
- add new voxel over selected face;
- click any face to add a new voxel above it directly (no selection needed);
- customize voxel color and scale;
- generate cuboid;

## Installation

The add-on source lives in the `polovoxel/` package; build an installable
zip with the packaging script, then install that zip in Blender:

```sh
python3 scripts/publish.py
```

This writes `dist/polovoxel_<version>.zip` (see `docs/CLI.md` for flags like
`--version-bump` and `--output-dir`). Then in Blender:

- open `Edit / Preferences / Add-ons`;
- click `Install` and select the zip from `dist/`;
- click `Install Add-on`;
- enable the "Polovoxel" checkbox.

Iterating on the source instead of reinstalling a zip every time? See
[`docs/TESTING.md`](docs/TESTING.md) for a symlink-based workflow that picks
up edits without repackaging.

## How to use

- open `World` tab;
- choose a scale;
- choose a color;
- click: Add first voxel;
- select the voxel object, press `Tab` to enter Edit Mode, press `3` (or
  click the face-select icon in the header) to switch to Face select mode,
  then click a face to select it — that's the face the next voxel will be
  added onto;
- click: Add voxel above selected face;

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — package layout and layering rationale
- [`docs/BUGS.md`](docs/BUGS.md) — bug & code-smell audit of the original single-file add-on
- [`docs/TESTING.md`](docs/TESTING.md) — local install/reload/debug workflow
- [`docs/CLI.md`](docs/CLI.md) — `scripts/publish.py` packaging script reference
- [`docs/architecture/README.md`](docs/architecture/README.md) — PlantUML component & sequence diagrams

## Resources

### tutorial

- https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html
- https://prosperocoder.com/posts/blender/blender-object-in-python/
- https://levelup.gitconnected.com/build-a-blender-add-on-ready-to-scale-8c285f9f0a5
- https://www.youtube.com/watch?v=Y67eCfiqJQU

### setup blender console

- https://blender.stackexchange.com/questions/97976/python-script-fail-look-in-the-console-for-now

### change and apply material

- https://stackoverflow.com/questions/44878048/use-blender-change-material-color-with-python
- https://blender.stackexchange.com/questions/23433/how-to-assign-a-new-material-to-an-object-in-the-scene-from-python?newreg=8966fdb299cd42ee8ee47ca9134f14ba

### object selection

- https://blender.stackexchange.com/questions/128549/how-can-i-check-face-selection-in-edit-mode

### object manipulations

- https://blender.stackexchange.com/questions/215024/getting-the-last-object-created

### object creation

- https://gist.github.com/haxpor/198f6993a62a21279519fcd0fbb36726

### object and face coodinates

- https://blenderartists.org/t/absolute-coordinates/297611
- https://blender.stackexchange.com/questions/7071/python-absolute-position-of-face
- https://docs.blender.org/api/current/bmesh.types.html#bmesh.types.BMFace

### change blender mode

- https://blenderartists.org/t/toggle-edit-mode-and-toggle-selection-mode/503898/2

### icons

- https://gist.github.com/eliemichel/251731e6cc711340dfefe90fe7e38ac9

### operator properties and UI

- https://blenderartists.org/t/custom-operator-with-arguments/550526
- https://blender.stackexchange.com/questions/17751/how-display-and-use-operator-properties-in-a-python-blender-ui-panel
- https://docs.blender.org/api/current/bpy.props.html
- https://devtalk.blender.org/t/why-cant-we-display-operator-properties-within-a-panel/11698/2

### custom color property

- https://blender.stackexchange.com/questions/6984/color-as-custom-property

### toggle active object

- https://blenderartists.org/t/how-to-select-the-last-created-object-as-the-active-object/656146

### custom UI

- https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui
- https://gist.github.com/p2or/2947b1aa89141caae182526a8fc2bc5a

### operator shortcuts and shortcut properties

- https://blender.stackexchange.com/questions/196483/create-keyboard-shortcut-for-an-operator-using-python
- https://blender.stackexchange.com/questions/195823/how-to-keymap-a-custom-operator-with-properties

### property group

- https://docs.blender.org/api/current/bpy.types.PropertyGroup.html
- https://devtalk.blender.org/t/creating-and-accessing-propertygroup-instances/14332

### get blender mode

- https://blender.stackexchange.com/questions/21408/know-when-edit-mode-is-entered-by-script-python

### unselect edit mode

- https://blenderartists.org/t/problem-with-bpy-ops-mesh-select-all-in-edit-mode/560398
- https://blender.stackexchange.com/questions/52479/why-deselecting-an-already-selected-vertex-does-not-work

### add-on breaks blender

- https://blender.stackexchange.com/questions/204633/undo-breaks-my-addon

### pass trought when click

- https://blenderartists.org/t/trigger-action-through-mouseclick/674367/7
</content>
