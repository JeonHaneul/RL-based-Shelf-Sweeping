"""Portable-path and per-environment regression checks without Isaac Sim.

Array checks run source expressions/function bodies with a small NumPy adapter.
This is intentionally not an Isaac Sim or PyTorch integration test.
"""

import ast
import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SHELF = ROOT / 'source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/shelf'
SPEC = importlib.util.spec_from_file_location('sweep_paths', SHELF / 'src/asset_paths.py')
paths = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(paths)


class PathTests(unittest.TestCase):
    def test_defaults_are_independent_of_working_directory(self):
        original = Path.cwd()
        with patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as temporary:
            try:
                os.chdir(temporary)
                self.assertEqual(paths.repository_root(), ROOT)
                self.assertEqual(paths.resolve_asset('object.usd'), str(ROOT / 'assets/usd/object.usd'))
                self.assertEqual(paths.environment_config_path(), SHELF / 'src/environment.yaml')
            finally:
                os.chdir(original)

    def test_relative_and_absolute_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / 'robot.usd'
            with patch.dict(os.environ, {'SWEEP_ASSET_ROOT': 'custom-assets', 'SWEEP_ROBOT_USD': str(model),
                                         'SWEEP_ENVIRONMENT_CONFIG': 'config/custom.yaml'}, clear=True):
                self.assertEqual(paths.asset_root(), ROOT / 'custom-assets')
                self.assertEqual(paths.resolve_asset('default.usd', 'SWEEP_ROBOT_USD'), str(model))
                self.assertEqual(paths.environment_config_path(), ROOT / 'config/custom.yaml')

    def test_explicit_uri_is_not_converted_to_a_local_path(self):
        with patch.dict(os.environ, {}, clear=True):
            value = 'omniverse://example/assets/robot.usd'
            self.assertEqual(paths.resolve_asset(value), value)


class Array(np.ndarray):
    def clone(self):
        return self.copy()

    def long(self):
        return self.astype(np.int64)


def array(value):
    return np.asarray(value).view(Array)


TORCH = SimpleNamespace(round=np.round, arange=np.arange, tanh=np.tanh,
                        abs=np.abs, sum=lambda value, dim=None: np.sum(value, axis=dim))


class BatchIsolationTests(unittest.TestCase):
    def test_initial_goals_use_each_environment(self):
        source = ast.parse((SHELF / 'mdp/commands/position_command.py').read_text(encoding='utf-8'))
        state = np.zeros((3, 13))
        state[:, :3] = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        for name in ('DynamicObjectGoalPosCommand', 'GraspTargetPosCommand'):
            with self.subTest(command=name):
                cls = next(item for item in source.body if isinstance(item, ast.ClassDef) and item.name == name)
                init = next(item for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == '__init__')
                assignment = next(item for item in init.body if isinstance(item, ast.Assign)
                                  and isinstance(item.targets[0], ast.Attribute)
                                  and item.targets[0].attr == 'pos_command_e')
                expression = compile(ast.Expression(assignment.value), '<source goal expression>', 'eval')
                obj = SimpleNamespace(target_init_state_w=state, init_pos_offset=np.array([0, .18, 0]))
                result = eval(expression, {'self': obj})
                expected = state[:, :3] + (obj.init_pos_offset if name.startswith('Dynamic') else 0)
                self.assertEqual(result.shape, (3, 3))
                np.testing.assert_allclose(result, expected)

    def test_non_target_motion_penalty_is_local_to_each_environment(self):
        for module in ('reward_sweep.py', 'reward_random_sweep.py'):
            with self.subTest(module=module):
                source = ast.parse((SHELF / 'mdp' / module).read_text(encoding='utf-8'))
                function = next(item for item in source.body if isinstance(item, ast.FunctionDef)
                                and item.name == 'object_collision')
                # Preserve the executable body, omitting simulator type annotations/defaults.
                function.returns = None
                function.args.defaults = []
                for argument in function.args.args:
                    argument.annotation = None
                namespace = {'torch': TORCH}
                exec(compile(ast.Module(body=[function], type_ignores=[]), str(SHELF / 'mdp' / module), 'exec'), namespace)
                velocity = array(np.zeros((2, 3, 3)))
                velocity[0, 0, :] = 100  # Moving target must be excluded.
                velocity[1, 2, :] = 100  # Different target in the second environment.
                velocity[1, 0, 0] = .2   # Only this non-target motion should incur a penalty.
                collection = SimpleNamespace(data=SimpleNamespace(object_lin_vel_w=velocity))
                class Scene(dict):
                    num_envs = 2
                env = SimpleNamespace(scene=Scene(objects=collection), target_id=array([[0], [2]]))
                result = namespace['object_collision'](env, SimpleNamespace(name='objects'))
                self.assertEqual(result.shape, (2,))
                np.testing.assert_allclose(result, [0, np.tanh(.2)])
                self.assertEqual(velocity[0, 0, 0], 100)  # Input buffer remains unchanged.


if __name__ == '__main__':
    unittest.main()
