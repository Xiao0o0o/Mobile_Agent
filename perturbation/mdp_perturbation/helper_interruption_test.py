"""Tests for helper interruption perturbation env."""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from android_world.env import interface
from mdp_perturbation.helper_interruption import (
    HelperInterruptionPerturbationConfig,
)
from mdp_perturbation.helper_interruption import HelperInterruptionPerturbationEnv


class _Action:

  def __init__(self, action_type: str):
    self.action_type = action_type


class _FakeEnv(interface.AsyncEnv):

  def __init__(self):
    self._controller = self
    self._actions = []
    self._interaction_cache = ""

  def reset(self, go_home: bool = False) -> interface.State:
    del go_home
    return self.get_state()

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    del wait_to_stabilize
    return interface.State(
        pixels=np.zeros((12, 12, 3), dtype=np.uint8),
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
    return self._controller

  @property
  def foreground_activity_name(self) -> str:
    return "com.example/.MainActivity"

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return (12, 12)

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return (12, 12)

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
    return (0, 0, 12, 12)


class HelperInterruptionPerturbationEnvTest(unittest.TestCase):

  @mock.patch("mdp_perturbation.helper_interruption.time.sleep")
  @mock.patch("mdp_perturbation.helper_interruption.show_helper_interruption")
  def test_uses_profile_pool_when_configured(
      self,
      show_helper_interruption_mock,
      sleep_mock,
  ):
    env = HelperInterruptionPerturbationEnv(
        _FakeEnv(),
        HelperInterruptionPerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            profile_pool=("popup_permission",),
            wait_after_launch_sec=0.0,
        ),
    )

    env.execute_action(_Action("click"))
    state = env.get_state()

    show_helper_interruption_mock.assert_called_once()
    spec = show_helper_interruption_mock.call_args.args[0]
    self.assertEqual(spec.title, "Allow notifications?")
    self.assertEqual(
        state.auxiliaries["mdp_helper_interruption"]["profile_name"],
        "popup_permission",
    )
    sleep_mock.assert_not_called()


if __name__ == "__main__":
  unittest.main()
