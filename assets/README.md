# Local model setup

The original code refers to custom USD models on a local filesystem and an Omniverse server. Those models are absent from the available source repository. Empty placeholders or replacement shapes are not supplied because they would change the robot articulation, contact geometry, and training task.

Set `SWEEP_ASSET_ROOT` to a local folder, or use this repository's default `assets/usd/` folder. The expected relative entry files are:

| Model | Relative path | Override |
| --- | --- | --- |
| Robot | `Robots/UR5e/UR5e_v4.usd` | `SWEEP_ROBOT_USD` |
| Fixed-direction shelf | `speedrack/speedrack_shape.usd` | `SWEEP_SHELF_FIXED_USD` |
| Random-direction shelf | `speedrack/speedrack.usd` | `SWEEP_SHELF_RANDOM_USD` |
| Bottle | `Bottle_6/Bottle_6.usd` | Object YAML |
| Cup 1 | `Collected_Cup_1/Cup_1.usd` | Object YAML |
| Cup 2 | `Collected_Cup_4/Cup_4.usd` | Object YAML |
| Mug 1 | `Collected_Mug_2/Mug_2.usd` | Object YAML |
| Mug 2 | `Collected_Mug_3/Mug_3.usd` | Object YAML |
| Can | `Can_6/Can_6.usd` | Object YAML |

Relative override paths are resolved under `SWEEP_ASSET_ROOT`. Absolute paths are used directly. Set `SWEEP_ENVIRONMENT_CONFIG` to use another object-layout YAML file. Its `objects`, `pose`, `width`, and `id` mappings must remain consistent.

Copy each asset's complete dependency folder, including referenced USD layers, meshes, and textures. When exporting from Nucleus, collect dependencies and make references portable. An entry file alone is insufficient if it still refers to another user's server or directory.

The robot must expose the six UR5e arm joints, the Robotiq joints configured in `shelf/src/ur5e.py`, and the `base_link` and `robotiq_base_link` prims used by the frame transformers. The shelf surface and object poses are calibrated around a 1.05 m height. Do not substitute a generic robot or shelf without adapting these settings.

```bash
export SWEEP_ASSET_ROOT="/absolute/path/to/usd_files"
export SWEEP_ROBOT_USD="/absolute/path/to/UR5e_v4.usd"
python scripts/sweeping/check_setup.py --assets --mode random
```

The check reports missing local entry files. Internal USD dependencies, joint ordering, contacts, and resulting motion must still be checked in Isaac Sim. To share models in GitHub, add the complete model folders only when their redistribution terms allow it.
