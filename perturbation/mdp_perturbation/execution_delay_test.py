"""Tests for execution-delay perturbation."""

import unittest

from android_world.env import interface
from android_world.agents import new_json_action as json_action
from mdp_perturbation.execution_delay import ExecutionDelayPerturbationConfig
from mdp_perturbation.execution_delay import ExecutionDelayPerturbationEnv
import numpy as np


class _FakeEnv(interface.AsyncEnv):

  def __init__(self):
    self._pixels_a = np.full((220, 140, 3), 255, dtype=np.uint8)
    self._pixels_b = np.full((220, 140, 3), 180, dtype=np.uint8)
    self._state = interface.State(
        pixels=self._pixels_a.copy(),
        forest=None,
        ui_elements=[],
        auxiliaries={},
    )
    self._actions = []
    self._interaction_cache = ""

  @property
  def controller(self):
    return None

  def reset(self, go_home: bool = False) -> interface.State:
    del go_home
    self._state = interface.State(
        pixels=self._pixels_a.copy(),
        forest=None,
        ui_elements=[],
        auxiliaries={},
    )
    self._actions.clear()
    return self._state

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    del wait_to_stabilize
    return self._state

  def ask_question(self, question: str, timeout_seconds: float = -1.0):
    del question, timeout_seconds
    return None

  def execute_action(self, action) -> None:
    self._actions.append(action)
    self._state = interface.State(
        pixels=self._pixels_b.copy(),
        forest=None,
        ui_elements=[],
        auxiliaries={},
    )

  @property
  def foreground_activity_name(self) -> str:
    return ""

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return (140, 220)

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return (140, 220)

  def close(self) -> None:
    return None

  @property
  def interaction_cache(self) -> str:
    return self._interaction_cache

  @interaction_cache.setter
  def interaction_cache(self, value: str) -> None:
    self._interaction_cache = value

  def hide_automation_ui(self) -> None:
    return None

  @property
  def orientation(self) -> int:
    return 0

  @property
  def physical_frame_boundary(self) -> tuple[int, int, int, int]:
    return (0, 0, 140, 220)


class ExecutionDelayPerturbationEnvTest(unittest.TestCase):

  def test_loading_delay_returns_overlay_before_final_state(self):
    env = ExecutionDelayPerturbationEnv(
        _FakeEnv(),
        ExecutionDelayPerturbationConfig(enabled=True, trigger_steps=(1,), delay_steps=2),
    )
    before = env.get_state(wait_to_stabilize=False)
    env.execute_action(json_action.JSONAction(action_type=json_action.WAIT))
    during = env.get_state(wait_to_stabilize=False)
    self.assertIn("mdp_execution_delay", during.auxiliaries)
    self.assertFalse(np.array_equal(during.pixels, before.pixels))
    after = env.get_state(wait_to_stabilize=False)
    final = env.get_state(wait_to_stabilize=False)
    self.assertNotIn("mdp_execution_delay", final.auxiliaries)
    self.assertTrue(np.array_equal(final.pixels, env._base_env._pixels_b))

  def test_block_actions_while_pending(self):
    env = ExecutionDelayPerturbationEnv(
        _FakeEnv(),
        ExecutionDelayPerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            delay_steps=2,
            block_actions_while_pending=True,
        ),
    )
    env.get_state(wait_to_stabilize=False)
    env.execute_action(json_action.JSONAction(action_type=json_action.WAIT))
    env.get_state(wait_to_stabilize=False)
    env.execute_action(json_action.JSONAction(action_type=json_action.WAIT))
    self.assertEqual(len(env._base_env._actions), 1)


if __name__ == "__main__":
  unittest.main()
