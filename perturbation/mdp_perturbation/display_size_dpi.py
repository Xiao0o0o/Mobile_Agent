"""Display-size and DPI perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import time

from android_world.env import interface
from mdp_perturbation.android_system_utils import clamp_int
from mdp_perturbation.android_system_utils import dict_without_none
from mdp_perturbation.android_system_utils import normalize_activation_mode
from mdp_perturbation.android_system_utils import read_wm_density
from mdp_perturbation.android_system_utils import read_wm_size
from mdp_perturbation.android_system_utils import reset_wm_density
from mdp_perturbation.android_system_utils import reset_wm_size
from mdp_perturbation.android_system_utils import set_wm_density
from mdp_perturbation.android_system_utils import set_wm_size


@dataclasses.dataclass(frozen=True)
class DisplaySizeDpiPerturbationConfig:
  """Configuration for real emulator display size / density switching."""

  enabled: bool = False
  activation_mode: str = "on_steps"
  trigger_steps: tuple[int, ...] = (3,)
  density_scale: float = 0.85
  size_scale: float = 0.94
  settle_time_sec: float = 1.2
  restore_on_close: bool = True

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      activation_mode: str,
      trigger_steps: str,
      density_scale: float,
      size_scale: float,
      settle_time_sec: float,
      restore_on_close: bool,
  ) -> "DisplaySizeDpiPerturbationConfig":
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
        density_scale=max(density_scale, 0.4),
        size_scale=max(size_scale, 0.4),
        settle_time_sec=max(settle_time_sec, 0.0),
        restore_on_close=restore_on_close,
    )


class DisplaySizeDpiPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that changes wm density and display size."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: DisplaySizeDpiPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_display_metadata: dict[str, object] | None = None
    self._original_density = read_wm_density(self._base_env.controller)
    self._original_size = read_wm_size(self._base_env.controller)
    self._display_was_changed = False

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_display_metadata = None
    state = self._base_env.reset(go_home=go_home)
    if self._config.enabled and self._config.activation_mode == "on_reset":
      self._apply_display_profile(trigger_step=0, trigger_source="reset")
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
    self._apply_display_profile(trigger_step=current_step, trigger_source="step")

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
      if self._config.restore_on_close and self._display_was_changed:
        reset_wm_size(self._base_env.controller)
        reset_wm_density(self._base_env.controller)
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

  def _apply_display_profile(
      self,
      trigger_step: int,
      trigger_source: str = "step",
  ) -> None:
    before_density = read_wm_density(self._base_env.controller)
    before_size = read_wm_size(self._base_env.controller)
    target_density = clamp_int(
        before_density["effective_density"] * self._config.density_scale,
        minimum=120,
    )
    effective_width, effective_height = before_size["effective_size"]
    target_width = clamp_int(effective_width * self._config.size_scale, minimum=320)
    target_height = clamp_int(effective_height * self._config.size_scale, minimum=480)
    set_wm_size(self._base_env.controller, target_width, target_height)
    set_wm_density(self._base_env.controller, target_density)
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    after_density = read_wm_density(self._base_env.controller)
    after_size = read_wm_size(self._base_env.controller)
    self._display_was_changed = self._display_was_changed or (
        after_density["effective_density"] != before_density["effective_density"]
        or after_size["effective_size"] != before_size["effective_size"]
    )
    self._last_display_metadata = {
        "active": True,
        "activation_mode": self._config.activation_mode,
        "trigger_step": trigger_step,
        "trigger_source": trigger_source,
        "density_before": before_density["effective_density"],
        "density_after": after_density["effective_density"],
        "target_density": target_density,
        "size_before": before_size["effective_size"],
        "size_after": after_size["effective_size"],
        "target_size": (target_width, target_height),
    }

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    density_state = read_wm_density(self._base_env.controller)
    size_state = read_wm_size(self._base_env.controller)
    auxiliaries["mdp_display_size_dpi"] = dict_without_none(
        {
            "current_density": density_state["effective_density"],
            "original_density": self._original_density["effective_density"],
            "target_density_scale": self._config.density_scale,
            "current_size": size_state["effective_size"],
            "original_size": self._original_size["effective_size"],
            "target_size_scale": self._config.size_scale,
            "activation_mode": self._config.activation_mode,
            "display_changed": self._display_was_changed,
            **(self._last_display_metadata or {}),
        }
    )
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
