"""Screen-orientation perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import time

from android_world.env import adb_utils
from android_world.env import interface
from mdp_perturbation.android_system_utils import dict_without_none
from mdp_perturbation.android_system_utils import normalize_activation_mode
from mdp_perturbation.android_system_utils import read_system_setting
from mdp_perturbation.android_system_utils import restore_optional_system_setting


_VALID_ORIENTATIONS = frozenset(
    {"portrait", "landscape", "portrait_reversed", "landscape_reversed"}
)
_ORIENTATION_NAMES = {
    0: "portrait",
    1: "landscape",
    2: "portrait_reversed",
    3: "landscape_reversed",
}


@dataclasses.dataclass(frozen=True)
class OrientationPerturbationConfig:
  """Configuration for forced orientation changes."""

  enabled: bool = False
  activation_mode: str = "on_steps"
  trigger_steps: tuple[int, ...] = (3,)
  orientation_sequence: tuple[str, ...] = ("landscape",)
  settle_time_sec: float = 1.0
  restore_on_close: bool = True

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      activation_mode: str,
      trigger_steps: str,
      orientation_sequence: str,
      settle_time_sec: float,
      restore_on_close: bool,
  ) -> "OrientationPerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]

    raw_sequence = [
        item.strip().lower()
        for item in orientation_sequence.split(",")
        if item.strip()
    ]
    if not raw_sequence:
      raw_sequence = ["landscape"]
    invalid = [item for item in raw_sequence if item not in _VALID_ORIENTATIONS]
    if invalid:
      raise ValueError(
          f"Unsupported orientations: {invalid!r}; expected values in"
          f" {sorted(_VALID_ORIENTATIONS)}"
      )
    normalized_activation_mode = normalize_activation_mode(activation_mode)
    return cls(
        enabled=enabled,
        activation_mode=normalized_activation_mode,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        orientation_sequence=tuple(raw_sequence),
        settle_time_sec=max(settle_time_sec, 0.0),
        restore_on_close=restore_on_close,
    )


class OrientationPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that changes the emulator orientation."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: OrientationPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: list[int] = []
    self._last_orientation_metadata: dict[str, object] | None = None
    self._original_accelerometer_rotation = read_system_setting(
        self._base_env.controller, "system", "accelerometer_rotation"
    )
    self._original_user_rotation = read_system_setting(
        self._base_env.controller, "system", "user_rotation"
    )
    self._original_orientation_name = _ORIENTATION_NAMES.get(
        self._base_env.orientation, "portrait"
    )
    self._orientation_was_changed = False

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_orientation_metadata = None
    state = self._base_env.reset(go_home=go_home)
    if self._config.enabled and self._config.activation_mode == "on_reset":
      self._apply_orientation(
          trigger_step=0,
          target_orientation=self._config.orientation_sequence[0],
          trigger_source="reset",
      )
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

    self._activated_steps.append(current_step)
    sequence_index = (len(self._activated_steps) - 1) % len(
        self._config.orientation_sequence
    )
    self._apply_orientation(
        trigger_step=current_step,
        target_orientation=self._config.orientation_sequence[sequence_index],
        trigger_source="step",
    )

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
      if self._config.restore_on_close and self._orientation_was_changed:
        restore_optional_system_setting(
            self._base_env.controller,
            "system",
            "accelerometer_rotation",
            self._original_accelerometer_rotation,
        )
        restore_optional_system_setting(
            self._base_env.controller,
            "system",
            "user_rotation",
            self._original_user_rotation,
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

  def _apply_orientation(
      self,
      trigger_step: int,
      target_orientation: str,
      trigger_source: str = "step",
  ) -> None:
    before_orientation = _ORIENTATION_NAMES.get(
        self._base_env.orientation, str(self._base_env.orientation)
    )
    adb_utils.change_orientation(target_orientation, self._base_env.controller)
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    after_orientation = _ORIENTATION_NAMES.get(
        self._base_env.orientation, str(self._base_env.orientation)
    )
    self._orientation_was_changed = (
        self._orientation_was_changed or before_orientation != after_orientation
    )
    self._last_orientation_metadata = {
        "active": True,
        "activation_mode": self._config.activation_mode,
        "trigger_step": trigger_step,
        "trigger_source": trigger_source,
        "orientation_before": before_orientation,
        "orientation_after": after_orientation,
        "target_orientation": target_orientation,
    }

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_orientation"] = dict_without_none(
        {
            "current_orientation": _ORIENTATION_NAMES.get(
                self._base_env.orientation, self._base_env.orientation
            ),
            "original_orientation": self._original_orientation_name,
            "activation_mode": self._config.activation_mode,
            "orientation_changed": self._orientation_was_changed,
            "orientation_sequence": self._config.orientation_sequence,
            **(self._last_orientation_metadata or {}),
        }
    )
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
