"""Tests for app-hang perturbation."""

from __future__ import annotations

import unittest
from unittest import mock

from android_world.agents import new_json_action as json_action
from android_world.env import interface
from mdp_perturbation.app_hang import AppHangPerturbationConfig
from mdp_perturbation.app_hang import AppHangPerturbationEnv
from mdp_perturbation.app_hang import _which_hang_button
import numpy as np


def _find_button_point(width: int, height: int, target: str) -> tuple[int, int]:
  for y in range(height):
    for x in range(width):
      if _which_hang_button(width, height, x, y) == target:
        return (x, y)
  raise AssertionError(f"Unable to find button point for {target!r}")


class _FakeEnv(interface.AsyncEnv):

  def __init__(self):
    self._pixels = np.full((220, 140, 3), 245, dtype=np.uint8)
    self._state = interface.State(
        pixels=self._pixels.copy(),
        forest=None,
        ui_elements=[],
        auxiliaries={},
    )
    self._actions = []
    self._interaction_cache = ""
    self._foreground_activity_name = "com.example.app/.MainActivity"

  def reset(self, go_home: bool = False) -> interface.State:
    del go_home
    self._actions.clear()
    self._foreground_activity_name = "com.example.app/.MainActivity"
    self._state = interface.State(
        pixels=self._pixels.copy(),
        forest=None,
        ui_elements=[],
        auxiliaries={},
    )
    return self._state

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    del wait_to_stabilize
    return self._state

  def ask_question(self, question: str, timeout_seconds: float = -1.0):
    del question, timeout_seconds
    return None

  def execute_action(self, action) -> None:
    self._actions.append(action)
    if getattr(action, "action_type", None) == json_action.OPEN_APP:
      self._foreground_activity_name = "com.example.app/.MainActivity"
    elif getattr(action, "action_type", None) == json_action.NAVIGATE_HOME:
      self._foreground_activity_name = "com.android.launcher/.Launcher"

  @property
  def controller(self):
    return self

  @property
  def foreground_activity_name(self) -> str:
    return self._foreground_activity_name

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


class AppHangPerturbationEnvTest(unittest.TestCase):

  def setUp(self):
    self.base_env = _FakeEnv()

  @mock.patch("mdp_perturbation.app_hang.time.sleep")
  def test_triggered_hang_swallow_actions_until_recovery(self, _mock_sleep):
    env = AppHangPerturbationEnv(
        self.base_env,
        AppHangPerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            settle_time_sec=0.0,
        ),
    )

    env.reset()
    env.execute_action(json_action.JSONAction(action_type=json_action.WAIT))
    hanging_state = env.get_state()

    self.assertEqual(len(self.base_env._actions), 0)
    self.assertTrue(hanging_state.auxiliaries["mdp_app_hang"]["hang_active"])
    self.assertFalse(np.array_equal(hanging_state.pixels, self.base_env._pixels))

    env.execute_action(json_action.JSONAction(action_type=json_action.WAIT))
    state_after_ignored_action = env.get_state()

    self.assertEqual(len(self.base_env._actions), 0)
    self.assertEqual(
        state_after_ignored_action.auxiliaries["mdp_app_hang"]["ignored_action_type"],
        json_action.WAIT,
    )

  @mock.patch("mdp_perturbation.app_hang.time.sleep")
  @mock.patch("mdp_perturbation.app_hang.issue_shell_command")
  def test_restart_button_force_stops_and_relaunches(
      self,
      mock_issue_shell_command,
      _mock_sleep,
  ):
    env = AppHangPerturbationEnv(
        self.base_env,
        AppHangPerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            settle_time_sec=0.0,
        ),
    )

    env.reset()
    env.execute_action(json_action.JSONAction(action_type=json_action.WAIT))
    restart_x, restart_y = _find_button_point(140, 220, "restart")

    env.execute_action(
        json_action.JSONAction(
            action_type=json_action.CLICK,
            x=restart_x,
            y=restart_y,
        )
    )
    recovered_state = env.get_state()

    mock_issue_shell_command.assert_has_calls(
        [
            mock.call(self.base_env.controller, "am", "force-stop", "com.example.app"),
            mock.call(
                self.base_env.controller,
                "monkey",
                "-p",
                "com.example.app",
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ),
        ]
    )
    self.assertTrue(recovered_state.auxiliaries["mdp_app_hang"]["recovered"])
    self.assertEqual(
        recovered_state.auxiliaries["mdp_app_hang"]["recovery_action"],
        "overlay_restart_button",
    )


if __name__ == "__main__":
  unittest.main()
