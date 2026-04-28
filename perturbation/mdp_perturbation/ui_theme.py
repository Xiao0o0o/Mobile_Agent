"""UI-theme perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import re
import time

from android_world.env import adb_utils
from android_world.env import interface
from mdp_perturbation.android_system_utils import normalize_activation_mode


_VALID_THEME_MODES = frozenset({"light", "dark"})
_THEME_MODE_TO_UIMODE = {
    "light": "no",
    "dark": "yes",
}
_UIMODE_TO_THEME_MODE = {
    "no": "light",
    "yes": "dark",
}


@dataclasses.dataclass(frozen=True)
class UIThemePerturbationConfig:
  """Configuration for real emulator UI theme switching."""

  enabled: bool = False
  activation_mode: str = "on_steps"
  trigger_steps: tuple[int, ...] = (3,)
  theme_mode: str = "dark"
  settle_time_sec: float = 1.0
  restore_on_close: bool = True

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      activation_mode: str,
      trigger_steps: str,
      theme_mode: str,
      settle_time_sec: float,
      restore_on_close: bool,
  ) -> "UIThemePerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]
    normalized_mode = theme_mode.strip().lower()
    if normalized_mode not in _VALID_THEME_MODES:
      raise ValueError(
          "theme_mode must be one of "
          f"{sorted(_VALID_THEME_MODES)}; got {theme_mode!r}."
      )
    normalized_activation_mode = normalize_activation_mode(activation_mode)
    return cls(
        enabled=enabled,
        activation_mode=normalized_activation_mode,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        theme_mode=normalized_mode,
        settle_time_sec=max(settle_time_sec, 0.0),
        restore_on_close=restore_on_close,
    )


class UIThemePerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that toggles emulator light/dark theme."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: UIThemePerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_theme_metadata: dict[str, object] | None = None
    self._original_theme_mode = self._read_theme_mode()
    self._theme_was_changed = False

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_theme_metadata = None
    state = self._base_env.reset(go_home=go_home)
    if self._config.enabled and self._config.activation_mode == "on_reset":
      self._apply_theme_switch(trigger_step=0, trigger_source="reset")
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
    self._apply_theme_switch(trigger_step=current_step, trigger_source="step")

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
      if self._config.restore_on_close and self._theme_was_changed:
        self._set_theme_mode(self._original_theme_mode)
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

  def _apply_theme_switch(
      self,
      trigger_step: int,
      trigger_source: str = "step",
  ) -> None:
    before_mode = self._read_theme_mode()
    self._set_theme_mode(self._config.theme_mode)
    after_mode = self._read_theme_mode()
    self._theme_was_changed = after_mode != before_mode or self._theme_was_changed
    self._last_theme_metadata = {
        "active": True,
        "activation_mode": self._config.activation_mode,
        "trigger_step": trigger_step,
        "trigger_source": trigger_source,
        "theme_before": before_mode,
        "theme_after": after_mode,
        "target_theme": self._config.theme_mode,
    }

  def _read_theme_mode(self) -> str:
    response = adb_utils.issue_generic_request(
        ["shell", "cmd", "uimode", "night"],
        self._base_env.controller,
    )
    output = response.generic.output.decode("utf-8", errors="ignore")
    match = re.search(r"Night mode:\s*(yes|no)", output)
    if not match:
      raise RuntimeError(f"Unable to parse theme mode from adb output: {output!r}")
    return _UIMODE_TO_THEME_MODE[match.group(1)]

  def _set_theme_mode(self, theme_mode: str) -> None:
    adb_utils.issue_generic_request(
        ["shell", "cmd", "uimode", "night", _THEME_MODE_TO_UIMODE[theme_mode]],
        self._base_env.controller,
    )
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_ui_theme"] = {
        "current_theme": self._read_theme_mode(),
        "original_theme": self._original_theme_mode,
        "target_theme": self._config.theme_mode,
        "activation_mode": self._config.activation_mode,
        "theme_changed": self._theme_was_changed,
    }
    if self._last_theme_metadata is not None:
      auxiliaries["mdp_ui_theme"].update(self._last_theme_metadata)
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
