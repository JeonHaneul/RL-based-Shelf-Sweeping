#!/usr/bin/env python3
"""Check source syntax and optional local USD inputs without starting simulation."""

import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHELF = ROOT / 'source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/shelf'


def load_paths():
    spec = importlib.util.spec_from_file_location('sweep_asset_paths', SHELF / 'src/asset_paths.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', action='store_true', help='Also require local USD entry files.')
    parser.add_argument('--mode', choices=['fixed', 'random', 'both'], default='both')
    args = parser.parse_args()
    errors = []
    files = list(SHELF.rglob('*.py')) + list((ROOT / 'scripts/sweeping').glob('*.py'))
    files += list((ROOT / 'scripts/reinforcement_learning/rsl_rl').glob('*.py'))
    for file in files:
        try:
            ast.parse(file.read_text(encoding='utf-8-sig'), filename=str(file))
        except (SyntaxError, UnicodeError) as error:
            errors.append(f'{file.relative_to(ROOT)}: {error}')
    registration = (SHELF / 'config/ur5e/__init__.py').read_text(encoding='utf-8')
    for task in ['Isaac-Sweep-Object-UR5e-v0', 'Isaac-Sweep-Object-UR5e-Random-v0']:
        if task not in registration:
            errors.append(f'Missing task registration: {task}')
    print(f'Checked Python syntax in {len(files)} files and both task registrations.')
    if args.assets:
        paths = load_paths()
        entries = json.loads((ROOT / 'assets/required_assets.json').read_text(encoding='utf-8'))
        if os.environ.get('SWEEP_ENVIRONMENT_CONFIG'):
            try:
                import yaml
                config = yaml.safe_load(paths.environment_config_path().read_text(encoding='utf-8'))
                entries = [entry for entry in entries if 'variable' in entry]
                entries += [dict(name=name, path=path, mode='both') for name, path in config['objects'].items()]
            except (ImportError, OSError, ValueError, KeyError) as error:
                errors.append(f'Cannot validate custom environment YAML: {error}')
        for entry in entries:
            if args.mode != 'both' and entry['mode'] not in ('both', args.mode):
                continue
            path = paths.resolve_asset(entry['path'], entry.get('variable'))
            if '://' in path:
                errors.append(f'{entry["name"]}: URI is not a verified local asset: {path}')
            elif not Path(path).is_file():
                errors.append(f'{entry["name"]}: missing {path}')
        print('Asset checks cover entry files only. USD references, joints, and geometry require simulation validation.')
    for error in errors:
        print(f'ERROR: {error}')
    if errors:
        return 1
    print('Requested checks passed. This does not verify Isaac Sim execution or policy performance.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
