"""Portable paths for the shelf-sweeping task, without importing Isaac Sim."""

import os
from pathlib import Path


def repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / 'isaaclab.sh').is_file() and (parent / 'VERSION').is_file():
            return parent
    raise RuntimeError('Cannot locate the bundled Isaac Lab repository.')


def asset_root() -> Path:
    configured = os.environ.get('SWEEP_ASSET_ROOT')
    root = Path(configured).expanduser() if configured else repository_root() / 'assets/usd'
    return (root if root.is_absolute() else repository_root() / root).resolve()


def resolve_asset(relative_path: str, variable: str | None = None) -> str:
    """Resolve relative paths under the asset root and preserve explicit URIs."""
    value = os.environ.get(variable, '') if variable else ''
    value = value or relative_path
    if '://' in value:
        return value
    path = Path(value).expanduser()
    return str((path if path.is_absolute() else asset_root() / path).resolve())


def environment_config_path(path: str | Path | None = None) -> Path:
    value = path or os.environ.get('SWEEP_ENVIRONMENT_CONFIG')
    if not value:
        return Path(__file__).with_name('environment.yaml')
    resolved = Path(value).expanduser()
    return (resolved if resolved.is_absolute() else repository_root() / resolved).resolve()
