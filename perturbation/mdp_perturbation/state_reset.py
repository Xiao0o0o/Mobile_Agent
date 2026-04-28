"""State-reset perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import time

from android_world.env import adb_utils
from android_world.env import interface


@dataclasses.dataclass(frozen=True)
class StateResetPerturbationConfig:
  """Configuration for app-reset perturbation."""

  enabled: bool = False
  trigger_steps: tuple[int, ...] = (3,)
  return_home: bool = True
  settle_time_sec: float = 1.0

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      trigger_steps: str,
      return_home: bool,
      settle_time_sec: float,
  ) -> "StateResetPerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]
    return cls(
        enabled=enabled,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        return_home=return_home,
        settle_time_sec=max(settle_time_sec, 0.0),
    )


class StateResetPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that force-stops foreground app and returns home."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: StateResetPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_reset_metadata: dict[str, object] | None = None

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_reset_metadata = None
    state = self._base_env.reset(go_home=go_home)
    return self._decorate_state(state)

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    state = self._base_env.get_state(wait_to_stabilize=wait_to_stabilize)
    return self._decorate_state(state)

  def execute_action(self, action) -> None:
    action_type = getattr(action, "action_type", None)
    if action_type in ("answer", "status"):
      self._base_env.execute_action(action)
      return

    self._executed_action_count += 1
    self._base_env.execute_action(action)

    if not self._config.enabled:
      return

    current_step = self._executed_action_count
    if current_step not in self._config.trigger_steps:
      return
    if current_step in self._activated_steps:
      return

    self._activated_steps.add(current_step)
    self._reset_foreground_app(trigger_step=current_step)

  def display_message(self, message: str, header: str = "") -> None:
    self._base_env.display_message(message, header=header)

  def ask_question(
      self, question: str, timeout_seconds: float = -1.0
  ) -> str | None:
    return self._base_env.ask_question(question, timeout_seconds=timeout_seconds)

  @property
  def controller(self):
    return self._base_env.controller

  @property
  def foreground_activity_name(self) -> str:
    return self._base_env.foreground_activity_name

  @property
  def device_screen_size(self) -> tuple[int, int]:
    return self._base_env.device_screen_size

  @property
  def logical_screen_size(self) -> tuple[int, int]:
    return self._base_env.logical_screen_size

  def close(self) -> None:
    self._base_env.close()

  @property
  def interaction_cache(self) -> str:
    return self._base_env.interaction_cache

  @interaction_cache.setter
  def interaction_cache(self, value: str) -> None:
    self._base_env.interaction_cache = value

  def hide_automation_ui(self) -> None:
    self._base_env.hide_automation_ui()

  @property
  def orientation(self) -> int:
    return self._base_env.orientation

  @property
  def physical_frame_boundary(self) -> tuple[int, int, int, int]:
    return self._base_env.physical_frame_boundary

  def _reset_foreground_app(self, trigger_step: int) -> None:
    activity_name = self._base_env.foreground_activity_name
    package_name = ""
    if activity_name and "/" in activity_name:
      package_name = adb_utils.extract_package_name(activity_name)
      adb_utils.issue_generic_request(
          ["shell", "am", "force-stop", package_name],
          self._base_env.controller,
      )
    if self._config.return_home:
      adb_utils.press_home_button(self._base_env.controller)
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    self._last_reset_metadata = {
        "active": True,
        "trigger_step": trigger_step,
        "reset_activity": activity_name,
        "reset_package": package_name,
        "returned_home": self._config.return_home,
    }

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    if self._last_reset_metadata is not None:
      auxiliaries["mdp_state_reset"] = self._last_reset_metadata
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
