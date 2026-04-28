"""Tests for state-reset perturbation."""

import unittest
from unittest import mock

from mdp_perturbation.state_reset import StateResetPerturbationConfig
from mdp_perturbation.state_reset import StateResetPerturbationEnv


class _FakeState:

  def __init__(self):
    self.pixels = None
    self.forest = None
    self.ui_elements = []
    self.auxiliaries = {}


class _FakeEnv:

  def __init__(self):
    self.controller = object()
    self.foreground_activity_name = "com.android.settings/.Settings"
    self.device_screen_size = (100, 200)
    self.logical_screen_size = (100, 200)
    self.interaction_cache = ""
    self.orientation = 0
    self.physical_frame_boundary = (0, 0, 100, 200)
    self.actions = []

  def reset(self, go_home: bool = False):
    del go_home
    return _FakeState()

  def get_state(self, wait_to_stabilize: bool = False):
    del wait_to_stabilize
    return _FakeState()

  def execute_action(self, action):
    self.actions.append(action)

  def display_message(self, message: str, header: str = ""):
    del message, header

  def ask_question(self, question: str, timeout_seconds: float = -1.0):
    del question, timeout_seconds
    return None

  def close(self):
    return None

  def hide_automation_ui(self):
    return None


class StateResetPerturbationEnvTest(unittest.TestCase):

  @mock.patch("mdp_perturbation.state_reset.adb_utils.press_home_button")
  @mock.patch("mdp_perturbation.state_reset.adb_utils.issue_generic_request")
  def test_reset_force_stops_foreground_app(
      self,
      mock_issue_generic_request,
      mock_press_home_button,
  ):
    env = StateResetPerturbationEnv(
        _FakeEnv(),
        StateResetPerturbationConfig(enabled=True, trigger_steps=(1,)),
    )

    env.execute_action(object())

    mock_issue_generic_request.assert_called_once()
    mock_press_home_button.assert_called_once()


if __name__ == "__main__":
  unittest.main()
