"""Date/time format perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import time

from android_world.env import interface
from mdp_perturbation.android_system_utils import dict_without_none
from mdp_perturbation.android_system_utils import normalize_activation_mode
from mdp_perturbation.android_system_utils import put_system_setting
from mdp_perturbation.android_system_utils import read_system_setting
from mdp_perturbation.android_system_utils import restore_optional_system_setting


_VALID_TIME_FORMATS = frozenset({"12", "24"})


@dataclasses.dataclass(frozen=True)
class LocaleDateFormatPerturbationConfig:
  """Configuration for system date/time format perturbation."""

  enabled: bool = False
  activation_mode: str = "on_steps"
  trigger_steps: tuple[int, ...] = (3,)
  time_format: str = "24"
  date_format: str = "dd-MM-yyyy"
  settle_time_sec: float = 1.0
  restore_on_close: bool = True

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      activation_mode: str,
      trigger_steps: str,
      time_format: str,
      date_format: str,
      settle_time_sec: float,
      restore_on_close: bool,
  ) -> "LocaleDateFormatPerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]
    normalized_time_format = time_format.strip()
    if normalized_time_format not in _VALID_TIME_FORMATS:
      raise ValueError(
          f"time_format must be one of {sorted(_VALID_TIME_FORMATS)}; got {time_format!r}."
      )
    normalized_activation_mode = normalize_activation_mode(activation_mode)
    normalized_date_format = date_format.strip() or "dd-MM-yyyy"
    return cls(
        enabled=enabled,
        activation_mode=normalized_activation_mode,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        time_format=normalized_time_format,
        date_format=normalized_date_format,
        settle_time_sec=max(settle_time_sec, 0.0),
        restore_on_close=restore_on_close,
    )


class LocaleDateFormatPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that changes system date/time display formats."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: LocaleDateFormatPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_format_metadata: dict[str, object] | None = None
    self._original_time_format_raw = read_system_setting(
        self._base_env.controller, "system", "time_12_24"
    )
    self._original_date_format_raw = read_system_setting(
        self._base_env.controller, "system", "date_format"
    )
    self._format_was_changed = False

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_format_metadata = None
    state = self._base_env.reset(go_home=go_home)
    if self._config.enabled and self._config.activation_mode == "on_reset":
      self._apply_format_change(trigger_step=0, trigger_source="reset")
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
    self._apply_format_change(trigger_step=current_step, trigger_source="step")

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
      if self._config.restore_on_close and self._format_was_changed:
        restore_optional_system_setting(
            self._base_env.controller,
            "system",
            "time_12_24",
            self._original_time_format_raw,
        )
        restore_optional_system_setting(
            self._base_env.controller,
            "system",
            "date_format",
            self._original_date_format_raw,
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

  def _apply_format_change(
      self,
      trigger_step: int,
      trigger_source: str = "step",
  ) -> None:
    before_time = read_system_setting(
        self._base_env.controller,
        "system",
        "time_12_24",
    )
    before_date = read_system_setting(
        self._base_env.controller,
        "system",
        "date_format",
    )
    put_system_setting(
        self._base_env.controller,
        "system",
        "time_12_24",
        self._config.time_format,
    )
    put_system_setting(
        self._base_env.controller,
        "system",
        "date_format",
        self._config.date_format,
    )
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    after_time = read_system_setting(
        self._base_env.controller,
        "system",
        "time_12_24",
    )
    after_date = read_system_setting(
        self._base_env.controller,
        "system",
        "date_format",
    )
    self._format_was_changed = self._format_was_changed or (
        before_time != after_time or before_date != after_date
    )
    self._last_format_metadata = {
        "active": True,
        "activation_mode": self._config.activation_mode,
        "trigger_step": trigger_step,
        "trigger_source": trigger_source,
        "time_format_before": before_time,
        "time_format_after": after_time,
        "date_format_before": before_date,
        "date_format_after": after_date,
        "target_time_format": self._config.time_format,
        "target_date_format": self._config.date_format,
    }

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_locale_date_format"] = dict_without_none(
        {
            "current_time_format": read_system_setting(
                self._base_env.controller,
                "system",
                "time_12_24",
            ),
            "current_date_format": read_system_setting(
                self._base_env.controller,
                "system",
                "date_format",
            ),
            "original_time_format": self._original_time_format_raw,
            "original_date_format": self._original_date_format_raw,
            "activation_mode": self._config.activation_mode,
            "format_changed": self._format_was_changed,
            **(self._last_format_metadata or {}),
        }
    )
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
