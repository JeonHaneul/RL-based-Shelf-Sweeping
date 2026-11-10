# Sweeping implementation

Paths in this document are relative to `source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/shelf/` unless specified otherwise.

## Execution flow

1. `scripts/reinforcement_learning/rsl_rl/train.py` launches Isaac Sim and loads the registered task and PPO configuration.
2. `config/ur5e/` configures the UR5e, joint actions, scene assets, and fixed or random sweep direction.
3. Reset events place six objects in two rows, choose a target, and set its lateral goal offset. Target and direction selection are shared within each reset batch in the current implementation.
4. The observation manager concatenates robot, target, end-effector, action-history, and goal information. PPO predicts six arm position actions and one binary gripper action.
5. Physics advances, rewards and termination conditions are evaluated, and completed environments reset. RSL-RL saves checkpoints and logs under `logs/rsl_rl/`.
6. `play.py` restores a matching policy checkpoint for simulation playback and exports the policy. This repository does not provide a physical UR5e deployment controller.

## Observation and action layout

The policy observes joint positions, joint velocities, the previous action, target position relative to the robot, target width, end-effector position and quaternion relative to the robot, and the target goal relative to the robot. See `mdp/observations.py` and `ObservationsCfg` in the task environment configuration for the exact ordering.

The source slices the first eight joint positions and first six joint velocities. Joint ordering and frame names must match the original robot USD. The arm action uses a position scale of 0.5 with the default joint offset. The single binary gripper command controls the configured Robotiq joints.

The nominal physics time step is 0.01 s with action decimation 2, giving a 50 Hz policy step. The configured episode length is 10 s, and the lateral target displacement is 0.18 m. These settings describe the source configuration, not a measured execution rate.

## PPO configurations

| Setting | Fixed direction | Random direction |
| --- | --- | --- |
| Rollout steps per environment | 36 | 36 |
| Maximum iterations | 30,000 | 62,000 |
| Checkpoint interval | 50 | 50 |
| Actor and critic hidden layers | 256, 128, 64 | 256, 128, 64 |
| Activation | ELU | ELU |
| Learning rate | 0.001, adaptive | 0.001, adaptive |
| Learning epochs / mini-batches | 8 / 4 | 8 / 4 |
| Discount factor | 0.95 | 0.98 |
| GAE lambda | 0.95 | 0.95 |
| Entropy coefficient | 0.01 | 0.005 |
| Desired KL | 0.02 | 0.02 |

The two task configurations also differ in reward weights and shelf assets. Use the configuration associated with a checkpoint when replaying it.

## Rewards and termination

Rewards combine reaching the target, aligning the hand, moving the target toward its goal, and returning toward the initial posture. Penalties discourage action changes, arm joint speed, motion of non-target objects, and shelf disturbance or inadequate clearance. The current homing reward compares the first five joints with their initial values.

Termination checks cover timeout, objects falling below the configured surface threshold, excessive tilt, excessive target velocity, shelf motion or clearance violations, and excessive arm joint velocity. Geometry-dependent thresholds assume the original shelf and object models. These are training episode conditions and do not implement real-robot emergency stopping.

## Changes in this distribution

- Replaced personal absolute paths and the custom robot's Nucleus URL with repository-relative paths and environment-variable overrides. The USD files themselves were not present in the source snapshot.
- Removed generated editor configuration containing machine-specific paths. Editor templates remain available.
- Corrected target-goal initialization to retain the environment dimension after selecting each target's state. Previously, indexing the already selected state again selected the first environment's position.
- Corrected the non-target motion penalty in both reward modules to reduce over objects and velocity components only. Previously, reducing over every dimension mixed parallel environments into one scalar penalty.
- Kept the bundled Isaac Lab framework, its task-specific buffers, license files, and attribution. Source provenance is recorded in `THIRD_PARTY_NOTICES.md` at the repository root.

The two tensor corrections change training behavior relative to the imported snapshot. No claim is made that newly trained policies reproduce previous experimental results.

## Checks and remaining validation

```bash
python scripts/sweeping/check_setup.py
python -m unittest discover -s scripts/sweeping/tests -v
python scripts/sweeping/check_setup.py --assets --mode random
```

The unit tests use NumPy to execute the relevant array expressions and reward function bodies without importing the simulator. They check per-environment isolation and portable path resolution. They do not validate PyTorch device placement, Isaac Sim APIs, USD composition, or policy performance.

The asset check verifies expected entry files. Full validation still requires the original USD assets and their dependencies, a compatible simulator/GPU, a short training run, and playback of the resulting checkpoint. No experiment-specific USD model or trained checkpoint is included.
