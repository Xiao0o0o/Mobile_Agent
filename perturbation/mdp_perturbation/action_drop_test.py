"""Tests for action-drop perturbation."""

import unittest

import numpy as np

from android_world.env import interface
from mdp_perturbation.action_drop import ActionDropPerturbationConfig
from mdp_perturbation.action_drop import ActionDropPerturbationEnv


class _Action:

  def __init__(self, action_type: str):
    self.action_type = action_type


class _FakeEnv(interface.AsyncEnv):

  def __init__(self):
    self._actions = []
    self._interaction_cache = ""

  def reset(self, go_home: bool = False) -> interface.State:
    del go_home
    return self.get_state()

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    del wait_to_stabilize
    return interface.State(
        pixels=np.zeros((8, 8, 3), dtype=np.uint8),
        forest=None,
        ui_elements=[],
        auxiliaries={},
    )

  def execute_action(self, action) -> None:
    self._actions.append(action)

  def display_message(self, message: str, header: str = "") -> None:
    del message, header

  def ask_question(
      self, question: str, timeout_seconds: float = -1.0
  ) -> str | None:
    del question, timeout_seconds
    return None

  @property
  def controller(self):
    return None

  @property
  def foreground_activity_name(self) -> str:
    return ""

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return (8, 8)

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return (8, 8)

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
    return (0, 0, 8, 8)


class ActionDropPerturbationEnvTest(unittest.TestCase):

  def test_drops_actions_when_probability_is_one(self):
    env = ActionDropPerturbationEnv(
        _FakeEnv(),
        ActionDropPerturbationConfig.from_values(
            enabled=True,
            drop_probability=1.0,
            seed=0,
        ),
    )

    env.execute_action(_Action("click"))
    state = env.get_state()

    self.assertEqual(len(env._base_env._actions), 0)
    self.assertEqual(
        state.auxiliaries["mdp_action_drop"]["dropped_action_count"], 1
    )
    self.assertTrue(
        state.auxiliaries["mdp_action_drop"]["last_event"]["dropped"]
    )

  def test_never_drops_answer_actions(self):
    env = ActionDropPerturbationEnv(
        _FakeEnv(),
        ActionDropPerturbationConfig.from_values(
            enabled=True,
            drop_probability=1.0,
            seed=0,
        ),
    )

    env.execute_action(_Action("answer"))

    self.assertEqual(len(env._base_env._actions), 1)


if __name__ == "__main__":
  unittest.main()
