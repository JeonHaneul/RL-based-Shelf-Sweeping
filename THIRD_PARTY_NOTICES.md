# Source provenance and licenses

This repository packages the shelf-sweeping source from [Holiclife-KTH/RL_based_Manipulation](https://github.com/Holiclife-KTH/RL_based_Manipulation), snapshot `466b683b33e504aff23a8825658f676f175d3bfc`. The source includes contributions recorded in that upstream repository. Packaging and repository maintenance by Haneul Jeon do not replace the original source authorship.

The included Isaac Lab framework identifies itself as version 2.2.1 and originates from [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab). Its source headers, [BSD-3-Clause license](LICENSE), [Apache-2.0 license for Mimic](LICENSE-mimic), [contributor list](CONTRIBUTORS.md), and [dependency notices](docs/licenses) are retained. The previous framework README and citation metadata are preserved under `docs/upstream/`.

RSL-RL 3.0.1 and the other Python dependencies are installed as packages. They are not Git submodules and their code is not relabeled as project-owned code. Isaac Sim is a separate installation with its own terms.

The custom USD models and trained policies were not present in the source snapshot. This repository does not assign a new license to absent models or claim to redistribute them.
