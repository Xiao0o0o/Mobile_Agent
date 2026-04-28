"""Action-drop perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import random

from android_world.env import interface


@dataclasses.dataclass(frozen=True)
class ActionDropPerturbationConfig:
  """Configuration for randomly dropping agent actions."""

  enabled: bool = False
  drop_probability: float = 0.0
  seed: int = 0

  @classmethod
  def from_values(
      cls,
      *,
      enabled: bool,
      drop_probability: float,
      seed: int,
  ) -> "ActionDropPerturbationConfig":
    return cls(
        enabled=enabled,
        drop_probability=min(max(drop_probability, 0.0), 1.0),
        seed=seed,
    )


class ActionDropPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that randomly skips executing actions."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: ActionDropPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._rng = random.Random(config.seed)
    self._attempted_action_count = 0
    self._dropped_action_count = 0
    self._last_drop_metadata: dict[str, object] | None = None

  def reset(self, go_home: bool = False) -> interface.State:
    self._attempted_action_count = 0
    self._dropped_action_count = 0
    self._last_drop_metadata = None
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
    should_drop = self._config.enabled and (
        self._rng.random() < self._config.drop_probability
    )
    if should_drop:
      self._dropped_action_count += 1
      self._last_drop_metadata = {
          "active": True,
          "attempted_step": self._attempted_action_count,
          "action_type": action_type,
          "dropped": True,
          "drop_probability": self._config.drop_probability,
      }
      return

    self._base_env.execute_action(action)
    self._last_drop_metadata = {
        "active": self._config.enabled,
        "attempted_step": self._attempted_action_count,
        "action_type": action_type,
        "dropped": False,
        "drop_probability": self._config.drop_probability,
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
    auxiliaries["mdp_action_drop"] = {
        "enabled": self._config.enabled,
        "drop_probability": self._config.drop_probability,
        "attempted_action_count": self._attempted_action_count,
        "dropped_action_count": self._dropped_action_count,
        "last_event": dict(self._last_drop_metadata or {}),
    }
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )
