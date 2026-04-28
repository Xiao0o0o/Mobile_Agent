"""Tests for UI-theme perturbation."""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from android_world.env import interface
from mdp_perturbation.ui_theme import UIThemePerturbationConfig
from mdp_perturbation.ui_theme import UIThemePerturbationEnv


class _FakeResponse:

  def __init__(self, text: str):
    self.generic = type("Generic", (), {"output": text.encode("utf-8")})()


class _FakeEnv(interface.AsyncEnv):

  def __init__(self):
    self._controller = object()
    self._theme_mode = "light"
    self._last_action = None
    self._interaction_cache = ""

  def reset(self, go_home: bool = False) -> interface.State:
    return self.get_state()

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    return interface.State(
        pixels=np.zeros((10, 10, 3), dtype=np.uint8),
        forest=None,
        ui_elements=None,
        auxiliaries={},
    )

  def execute_action(self, action) -> None:
    self._last_action = action

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
  def interaction_cache(self) -> str:
    return self._interaction_cache

  @interaction_cache.setter
  def interaction_cache(self, value: str) -> None:
    self._interaction_cache = value

  @property
  def foreground_activity_name(self) -> str:
    return "com.android.settings/.Settings"

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return (1080, 2400)

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return (1080, 2400)

  def close(self) -> None:
    return

  def hide_automation_ui(self) -> None:
    return

  @property
  def orientation(self) -> int:
    return 0

  @property
  def physical_frame_boundary(self) -> tuple[int, int, int, int]:
    return (0, 0, 1080, 2400)


class UIThemePerturbationEnvTest(unittest.TestCase):

  def setUp(self):
    self.base_env = _FakeEnv()

    def _fake_issue_generic_request(args, env, timeout_sec=0.0):
      del env, timeout_sec
      if args[:4] == ["shell", "cmd", "uimode", "night"] and len(args) == 4:
        mode = "yes" if self.base_env._theme_mode == "dark" else "no"
        return _FakeResponse(f"Night mode: {mode}\n")
      if args[:4] == ["shell", "cmd", "uimode", "night"] and len(args) == 5:
        self.base_env._theme_mode = "dark" if args[4] == "yes" else "light"
        mode = "yes" if self.base_env._theme_mode == "dark" else "no"
        return _FakeResponse(f"Night mode: {mode}\n")
      raise AssertionError(f"Unexpected adb args: {args!r}")

    self.issue_request_patch = mock.patch(
        "mdp_perturbation.ui_theme.adb_utils.issue_generic_request",
        side_effect=_fake_issue_generic_request,
    )
    self.sleep_patch = mock.patch("mdp_perturbation.ui_theme.time.sleep")
    self.issue_request_patch.start()
    self.sleep_patch.start()
    self.addCleanup(self.issue_request_patch.stop)
    self.addCleanup(self.sleep_patch.stop)

  def test_switches_theme_on_trigger_step(self):
    wrapped_env = UIThemePerturbationEnv(
        self.base_env,
        UIThemePerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            theme_mode="dark",
            settle_time_sec=0.0,
            restore_on_close=False,
        ),
    )

    wrapped_env.execute_action(object())
    state = wrapped_env.get_state()

    self.assertEqual(self.base_env._theme_mode, "dark")
    self.assertEqual(state.auxiliaries["mdp_ui_theme"]["theme_after"], "dark")
    self.assertEqual(state.auxiliaries["mdp_ui_theme"]["current_theme"], "dark")

  def test_switches_theme_on_reset_when_configured(self):
    wrapped_env = UIThemePerturbationEnv(
        self.base_env,
        UIThemePerturbationConfig(
            enabled=True,
            activation_mode="on_reset",
            theme_mode="dark",
            settle_time_sec=0.0,
            restore_on_close=False,
        ),
    )

    state = wrapped_env.reset()

    self.assertEqual(self.base_env._theme_mode, "dark")
    self.assertEqual(state.auxiliaries["mdp_ui_theme"]["trigger_source"], "reset")
    self.assertEqual(state.auxiliaries["mdp_ui_theme"]["current_theme"], "dark")

  def test_restores_original_theme_on_close(self):
    wrapped_env = UIThemePerturbationEnv(
        self.base_env,
        UIThemePerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            theme_mode="dark",
            settle_time_sec=0.0,
            restore_on_close=True,
        ),
    )

    wrapped_env.execute_action(object())
    wrapped_env.close()

    self.assertEqual(self.base_env._theme_mode, "light")


if __name__ == "__main__":
  unittest.main()
