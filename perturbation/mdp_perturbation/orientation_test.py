"""Tests for orientation perturbation."""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from android_world.env import interface
from mdp_perturbation.orientation import OrientationPerturbationConfig
from mdp_perturbation.orientation import OrientationPerturbationEnv


_ORIENTATION_TO_INT = {
    "portrait": 0,
    "landscape": 1,
    "portrait_reversed": 2,
    "landscape_reversed": 3,
}


class _FakeEnv(interface.AsyncEnv):

  def __init__(self):
    self._controller = self
    self._orientation = 0
    self._last_action = None
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
  def foreground_activity_name(self) -> str:
    return "com.example.app/.MainActivity"

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return (1080, 2400)

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return (1080, 2400)

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
    return self._orientation

  @property
  def physical_frame_boundary(self) -> tuple[int, int, int, int]:
    return (0, 0, 1080, 2400)


class OrientationPerturbationEnvTest(unittest.TestCase):

  def setUp(self):
    self.base_env = _FakeEnv()
    self.settings = {
        ("system", "accelerometer_rotation"): "1",
        ("system", "user_rotation"): "0",
    }
    self.restored_settings: list[tuple[str, str, str | None]] = []

    self.read_patch = mock.patch(
        "mdp_perturbation.orientation.read_system_setting",
        side_effect=lambda controller, namespace, key: self.settings.get(
            (namespace, key)
        ),
    )
    self.restore_patch = mock.patch(
        "mdp_perturbation.orientation.restore_optional_system_setting",
        side_effect=self._restore_setting,
    )
    self.change_patch = mock.patch(
        "mdp_perturbation.orientation.adb_utils.change_orientation",
        side_effect=self._change_orientation,
    )
    self.sleep_patch = mock.patch("mdp_perturbation.orientation.time.sleep")
    self.read_patch.start()
    self.restore_patch.start()
    self.change_patch.start()
    self.sleep_patch.start()
    self.addCleanup(self.read_patch.stop)
    self.addCleanup(self.restore_patch.stop)
    self.addCleanup(self.change_patch.stop)
    self.addCleanup(self.sleep_patch.stop)

  def _restore_setting(
      self,
      controller,
      namespace: str,
      key: str,
      value: str | None,
  ) -> None:
    del controller
    self.restored_settings.append((namespace, key, value))
    self.settings[(namespace, key)] = value

  def _change_orientation(self, orientation: str, controller) -> None:
    controller._orientation = _ORIENTATION_TO_INT[orientation]

  def test_changes_orientation_on_trigger_step(self):
    env = OrientationPerturbationEnv(
        self.base_env,
        OrientationPerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            orientation_sequence=("landscape",),
            settle_time_sec=0.0,
            restore_on_close=False,
        ),
    )

    env.execute_action(object())
    state = env.get_state()

    self.assertEqual(self.base_env.orientation, 1)
    self.assertEqual(
        state.auxiliaries["mdp_orientation"]["orientation_after"], "landscape"
    )
    self.assertEqual(
        state.auxiliaries["mdp_orientation"]["current_orientation"], "landscape"
    )
    self.assertTrue(state.auxiliaries["mdp_orientation"]["orientation_changed"])

  def test_applies_orientation_on_reset_when_configured(self):
    env = OrientationPerturbationEnv(
        self.base_env,
        OrientationPerturbationConfig(
            enabled=True,
            activation_mode="on_reset",
            orientation_sequence=("landscape",),
            settle_time_sec=0.0,
            restore_on_close=False,
        ),
    )

    state = env.reset()

    self.assertEqual(self.base_env.orientation, 1)
    self.assertEqual(
        state.auxiliaries["mdp_orientation"]["trigger_source"], "reset"
    )
    self.assertEqual(
        state.auxiliaries["mdp_orientation"]["current_orientation"], "landscape"
    )

  def test_restores_original_rotation_settings_on_close(self):
    env = OrientationPerturbationEnv(
        self.base_env,
        OrientationPerturbationConfig(
            enabled=True,
            trigger_steps=(1,),
            orientation_sequence=("landscape",),
            settle_time_sec=0.0,
            restore_on_close=True,
        ),
    )

    env.execute_action(object())
    env.close()

    self.assertIn(
        ("system", "accelerometer_rotation", "1"), self.restored_settings
    )
    self.assertIn(("system", "user_rotation", "0"), self.restored_settings)


if __name__ == "__main__":
  unittest.main()
