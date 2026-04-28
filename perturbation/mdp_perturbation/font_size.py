"""Font-size perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import time

from android_world.env import interface
from mdp_perturbation.android_system_utils import dict_without_none
from mdp_perturbation.android_system_utils import normalize_activation_mode
from mdp_perturbation.android_system_utils import read_font_scale
from mdp_perturbation.android_system_utils import restore_optional_system_setting
from mdp_perturbation.android_system_utils import put_system_setting


@dataclasses.dataclass(frozen=True)
class FontSizePerturbationConfig:
  """Configuration for real emulator font scaling."""

  enabled: bool = False
  activation_mode: str = "on_steps"
  trigger_steps: tuple[int, ...] = (3,)
  font_scale: float = 1.3
  settle_time_sec: float = 1.0
  restore_on_close: bool = True

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      activation_mode: str,
      trigger_steps: str,
      font_scale: float,
      settle_time_sec: float,
      restore_on_close: bool,
  ) -> "FontSizePerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]
    normalized_activation_mode = normalize_activation_mode(activation_mode)
    return cls(
        enabled=enabled,
        activation_mode=normalized_activation_mode,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        font_scale=max(font_scale, 0.5),
        settle_time_sec=max(settle_time_sec, 0.0),
        restore_on_close=restore_on_close,
    )


class FontSizePerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that changes the system font scale."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: FontSizePerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_font_metadata: dict[str, object] | None = None
    self._original_font_scale_raw, self._original_font_scale = read_font_scale(
        self._base_env.controller
    )
    self._font_scale_was_changed = False

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_font_metadata = None
    state = self._base_env.reset(go_home=go_home)
    if self._config.enabled and self._config.activation_mode == "on_reset":
      self._apply_font_scale(trigger_step=0, trigger_source="reset")
      state = self._base_env.get_state(wait_to_stabilize=False)
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

    if not self._config.enabled or self._config.activation_mode != "on_steps":
      return

    current_step = self._executed_action_count
    if current_step not in self._config.trigger_steps:
      return
    if current_step in self._activated_steps:
      return

    self._activated_steps.add(current_step)
    self._apply_font_scale(trigger_step=current_step, trigger_source="step")

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
    try:
      if self._config.restore_on_close and self._font_scale_was_changed:
        restore_optional_system_setting(
            self._base_env.controller,
            "system",
            "font_scale",
            self._original_font_scale_raw,
        )
        if self._config.settle_time_sec > 0:
          time.sleep(self._config.settle_time_sec)
    finally:
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

  def _apply_font_scale(
      self,
      trigger_step: int,
      trigger_source: str = "step",
  ) -> None:
    before_scale = read_font_scale(self._base_env.controller)[1]
    put_system_setting(
        self._base_env.controller,
        "system",
        "font_scale",
        f"{self._config.font_scale:.2f}",
    )
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    after_scale = read_font_scale(self._base_env.controller)[1]
    self._font_scale_was_changed = (
        self._font_scale_was_changed or abs(after_scale - before_scale) > 1e-6
    )
    self._last_font_metadata = {
        "active": True,
        "activation_mode": self._config.activation_mode,
        "trigger_step": trigger_step,
        "trigger_source": trigger_source,
        "font_scale_before": before_scale,
        "font_scale_after": after_scale,
        "target_font_scale": self._config.font_scale,
    }

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    current_font_scale = read_font_scale(self._base_env.controller)[1]
    auxiliaries["mdp_font_size"] = dict_without_none(
        {
            "current_font_scale": current_font_scale,
            "original_font_scale": self._original_font_scale,
            "target_font_scale": self._config.font_scale,
            "activation_mode": self._config.activation_mode,
            "font_scale_changed": self._font_scale_was_changed,
            **(self._last_font_metadata or {}),
        }
    )
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
