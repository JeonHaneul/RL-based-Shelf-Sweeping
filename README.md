# RL-based Shelf Sweeping

Reinforcement learning for non-prehensile object rearrangement on a shelf using a UR5e manipulator. The policy learns to approach a target, push it toward a lateral goal, and return the arm toward its initial posture. Training uses PPO with RSL-RL and the bundled Isaac Lab environment.

## Overview

| Stage | Implementation |
| --- | --- |
| Scene reset | Select a target, shuffle object placement, and configure the available sweeping direction |
| Observation | Robot joint state, previous action, target position and width, end-effector pose, and target goal |
| Action | Six arm joint-position commands and one binary gripper command |
| Reward | Reaching, hand orientation, object displacement, and homing, with motion and collision penalties |
| Episode termination | Timeout, object drop or tilt, target speed, shelf disturbance or clearance, and arm joint speed |

Two tasks are registered:

| Task ID | Direction | PPO configuration |
| --- | --- | --- |
| `Isaac-Sweep-Object-UR5e-v0` | Fixed sweep direction | `config/ur5e/agents/rsl_rl_ppo_cfg.py` |
| `Isaac-Sweep-Object-UR5e-Random-v0` | Random left or right direction | `config/ur5e/agents/rsl_rl_ppo_cfg_02.py` |

Both tasks randomize object placement. They use different reward and PPO settings, so they are not a controlled comparison that changes only the direction. The termination rules are simulation training conditions, not a real-robot safety controller.

## Repository layout

The task directory below is abbreviated as `shelf/`:
[`source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/shelf/`](source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/shelf).

| Path | Contents |
| --- | --- |
| `shelf/config/ur5e/` | Task registration, robot/action setup, and PPO configurations |
| `shelf/shelf_sweep*_env_cfg.py` | Scene, observations, rewards, terminations, and curriculum |
| `shelf/mdp/` | Reset logic, observations, goal commands, rewards, and termination functions |
| `shelf/src/` | Object layout, UR5e configuration, and portable asset paths |
| `scripts/reinforcement_learning/rsl_rl/` | Training, checkpoint playback, and policy export |
| `scripts/sweeping/` | Source and local-asset preflight checks |
| `assets/` | Required asset manifest and placement instructions |
| `source/isaaclab*`, `apps/` | Bundled Isaac Lab framework and simulator applications |

The Isaac Lab source is included directly. **There are no Git submodules to initialize.** This checkout contains task-specific environment buffers and should not be replaced with an arbitrary upstream Isaac Lab installation.

## Installation

The source targets **Isaac Lab 2.2.1, Isaac Sim 5.0.0, Python 3.11, and RSL-RL 3.0.1**. The Linux instructions below use Ubuntu 22.04 and an Isaac Sim-compatible NVIDIA GPU/driver. Actual training capacity depends on the GPU and the assets.

```bash
git clone https://github.com/JeonHaneul/RL-based-Shelf-Sweeping.git
cd RL-based-Shelf-Sweeping

conda create -n shelf-sweeping python=3.11 -y
conda activate shelf-sweeping
python -m pip install --upgrade pip
python -m pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
python -m pip install "isaacsim[all,extscache]==5.0.0" --extra-index-url https://pypi.nvidia.com
bash isaaclab.sh -i rsl_rl
python -m pip install PyYAML
```

The simulator and Python dependencies are installed separately. The first simulator launch can download additional extensions and assets. See the [version-specific installation guide](https://isaac-sim.github.io/IsaacLab/v2.2.1/source/setup/installation/pip_installation.html) for platform requirements.

## Local assets

**The source does not include the experiment-specific robot, shelf, or object USD models, or a trained checkpoint.** Provide the original models and their referenced meshes/textures before starting a simulation.

Place them under `assets/usd/`, or point to an existing directory:

```bash
export SWEEP_ASSET_ROOT="/absolute/path/to/usd_files"
python scripts/sweeping/check_setup.py --assets --mode random
```

[Asset setup](assets/README.md) lists the expected files and per-model overrides. Paths are resolved from the repository and asset root, without depending on a particular user's home directory. A source-only check is available without Isaac Sim:

```bash
python scripts/sweeping/check_setup.py
```

## Train and play

Run commands from the repository root with the environment activated and the assets configured. Start with a small run to check model compatibility:

```bash
bash isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task Isaac-Sweep-Object-UR5e-Random-v0 \
  --num_envs 16 --max_iterations 10 --headless
```

For training, increase `--num_envs` according to available GPU memory and choose the desired `--max_iterations`. Omit the latter to use the task configuration. To train the fixed-direction task, use `--task Isaac-Sweep-Object-UR5e-v0`.

Play a checkpoint trained with the same task:

```bash
bash isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task Isaac-Sweep-Object-UR5e-Random-v0 \
  --num_envs 1 --checkpoint /absolute/path/to/model.pt \
  env.observations.policy.enable_corruption=false
```

Runs are saved under `logs/rsl_rl/UR5e_shelf_sweep/` or `logs/rsl_rl/UR5e_shelf_sweep_random/`. The playback script also exports policy files beside the selected checkpoint. The original source contains playback configuration classes, but they are not registered as separate task IDs. The command above explicitly disables observation noise.

## Configuration and validation

Change object paths, poses, widths, and IDs in `shelf/src/environment.yaml`. Keep the original USD articulation/joint names, shelf geometry, and object dimensions consistent with the task settings. See [implementation notes](docs/sweeping-implementation.md) for the observation layout, PPO settings, and packaging fixes.

Source checks and regression checks for the packaging fixes are provided. A complete Isaac Sim training/playback run has not been validated in this release. Missing assets must be supplied before that validation can be completed.

Maintained by [Haneul Jeon](https://github.com/JeonHaneul). Bundled framework licenses and source provenance are recorded in [third-party notices](THIRD_PARTY_NOTICES.md).
