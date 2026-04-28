"""Action-delay perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import random
import time

from android_world.env import interface


@dataclasses.dataclass(frozen=True)
class ActionDelayPerturbationConfig:
  """Configuration for delaying action execution."""

  enabled: bool = False
  delay_probability: float = 0.0
  delay_seconds: float = 0.0
  seed: int = 0

  @classmethod
  def from_values(
      cls,
      *,
      enabled: bool,
      delay_probability: float,
      delay_seconds: float,
      seed: int,
  ) -> "ActionDelayPerturbationConfig":
    return cls(
        enabled=enabled,
        delay_probability=min(max(delay_probability, 0.0), 1.0),
        delay_seconds=max(delay_seconds, 0.0),
        seed=seed,
    )


class ActionDelayPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that sleeps before forwarding some actions."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: ActionDelayPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._rng = random.Random(config.seed)
    self._attempted_action_count = 0
    self._delayed_action_count = 0
    self._last_delay_metadata: dict[str, object] | None = None

  def reset(self, go_home: bool = False) -> interface.State:
    self._attempted_action_count = 0
    self._delayed_action_count = 0
    self._last_delay_metadata = None
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

    self._attempted_action_count += 1
    should_delay = (
        self._config.enabled
        and self._config.delay_seconds > 0.0
        and self._rng.random() < self._config.delay_probability
    )
    applied_delay = self._config.delay_seconds if should_delay else 0.0
    if should_delay:
      time.sleep(applied_delay)
      self._delayed_action_count += 1
    self._base_env.execute_action(action)
    self._last_delay_metadata = {
        "active": self._config.enabled,
        "attempted_step": self._attempted_action_count,
        "action_type": action_type,
        "delayed": should_delay,
        "delay_probability": self._config.delay_probability,
        "applied_delay_seconds": applied_delay,
    }

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

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_action_delay"] = {
        "enabled": self._config.enabled,
        "delay_probability": self._config.delay_probability,
        "delay_seconds": self._config.delay_seconds,
        "attempted_action_count": self._attempted_action_count,
        "delayed_action_count": self._delayed_action_count,
        "last_event": dict(self._last_delay_metadata or {}),
    }
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
