"""Helper-app powered interruption perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
import random
import time

from android_world.env import interface
from mdp_perturbation.helper_app import HelperInterruptionSpec
from mdp_perturbation.helper_app import show_helper_interruption


_HELPER_INTERRUPTION_PROFILES: dict[str, dict[str, object]] = {
    "bottom_sheet_consent": {
        "kind": "popup",
        "surface_style": "bottom_sheet",
        "app_name": "News Daily",
        "title": "Privacy choices",
        "message": (
            "Choose whether this app can use analytics and personalized content"
            " while you browse."
        ),
        "primary_button": "Accept",
        "secondary_button": "Manage options",
        "primary_action": "dismiss",
        "secondary_action": "open_destination",
        "secondary_destination": "privacy_options",
        "blocking": True,
    },
    "popup_permission": {
        "kind": "popup",
        "surface_style": "dialog",
        "app_name": "Android System",
        "title": "Allow notifications?",
        "message": "Android System wants to send alerts while you use this app.",
        "primary_button": "Allow",
        "secondary_button": "Not now",
        "primary_action": "open_destination",
        "primary_destination": "notification_settings",
        "secondary_action": "dismiss",
        "blocking": True,
    },
    "popup_security": {
        "kind": "popup",
        "surface_style": "dialog",
        "app_name": "Security Center",
        "title": "Verify this action",
        "message": "This app is trying to change a protected system setting.",
        "primary_button": "Continue",
        "secondary_button": "Cancel",
        "primary_action": "open_destination",
        "primary_destination": "security_center",
        "secondary_action": "dismiss",
        "blocking": True,
    },
    "interstitial_ad": {
        "kind": "ad",
        "surface_style": "interstitial",
        "app_name": "Market Hub",
        "title": "48-hour flash sale",
        "message": "Save 60% on travel gear if you check out before midnight.",
        "primary_button": "Shop now",
        "secondary_button": "Maybe later",
        "primary_action": "open_destination",
        "primary_destination": "shopping_amazon",
        "secondary_action": "dismiss",
        "blocking": True,
    },
    "ad_trial_offer": {
        "kind": "ad",
        "surface_style": "interstitial",
        "app_name": "ShopEasy",
        "title": "Try Premium for 30 days",
        "message": (
            "Unlock ad-free browsing, offline access, and exclusive themes."
        ),
        "primary_button": "Install",
        "secondary_button": "Close",
        "primary_action": "open_destination",
        "primary_destination": "app_store_update",
        "secondary_action": "dismiss",
        "blocking": True,
    },
    "rate_dialog": {
        "kind": "popup",
        "surface_style": "bottom_sheet",
        "app_name": "Notes Pro",
        "title": "Enjoying Notes Pro?",
        "message": (
            "Would you like to rate the app and tell us what is working well?"
        ),
        "primary_button": "Rate now",
        "secondary_button": "No thanks",
        "primary_action": "open_destination",
        "primary_destination": "rating_flow",
        "secondary_action": "dismiss",
        "blocking": True,
    },
    "update_system": {
        "kind": "update",
        "surface_style": "dialog",
        "app_name": "System updater",
        "title": "Update available",
        "message": (
            "A newer version is ready with security fixes and improved"
            " stability."
        ),
        "primary_button": "Update now",
        "secondary_button": "Later",
        "primary_action": "open_destination",
        "primary_destination": "system_update_settings",
        "secondary_action": "dismiss",
        "blocking": True,
    },
    "update_app_sheet": {
        "kind": "update",
        "surface_style": "bottom_sheet",
        "app_name": "Maps Go",
        "title": "New features are ready",
        "message": (
            "Get route previews, bug fixes, and improved battery performance."
        ),
        "primary_button": "Update",
        "secondary_button": "Skip",
        "primary_action": "open_destination",
        "primary_destination": "app_store_update",
        "secondary_action": "dismiss",
        "blocking": False,
    },
    "notification_message": {
        "kind": "notification",
        "surface_style": "banner",
        "app_name": "Messages",
        "title": "New message",
        "message": "Jordan: The meeting moved to 3:30 PM.",
        "primary_button": "Open",
        "secondary_button": "Dismiss",
        "primary_action": "open_destination",
        "primary_destination": "message_thread",
        "secondary_action": "dismiss",
        "blocking": False,
        "auto_dismiss_ms": 0,
    },
    "notification_delivery": {
        "kind": "notification",
        "surface_style": "banner",
        "app_name": "Parcel Tracker",
        "title": "Driver is nearby",
        "message": "Your package will arrive in the next 5 minutes.",
        "primary_button": "Track",
        "secondary_button": "Dismiss",
        "primary_action": "open_destination",
        "primary_destination": "delivery_tracking",
        "secondary_action": "dismiss",
        "blocking": False,
        "auto_dismiss_ms": 4000,
    },
}

VALID_HELPER_INTERRUPTION_PROFILE_STRATEGIES = frozenset({"cycle", "random"})


@dataclasses.dataclass(frozen=True)
class HelperInterruptionPerturbationConfig:
  """Configuration for launching the standalone helper-app interruption."""

  enabled: bool = False
  trigger_steps: tuple[int, ...] = (3,)
  kind: str = "popup"
  surface_style: str = ""
  app_name: str = "Android System"
  title: str = "Allow notifications?"
  message: str = "Android System wants to send alerts while you use this app."
  primary_button: str = "Allow"
  secondary_button: str = "Not now"
  blocking: bool = True
  auto_dismiss_ms: int = 0
  primary_action: str = ""
  secondary_action: str = ""
  primary_destination: str = ""
  secondary_destination: str = ""
  profile_pool: tuple[str, ...] = ()
  profile_seed: int = 0
  profile_strategy: str = "cycle"
  wait_after_launch_sec: float = 1.0

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      trigger_steps: str,
      kind: str,
      surface_style: str,
      app_name: str,
      title: str,
      message: str,
      primary_button: str,
      secondary_button: str,
      blocking: bool,
      auto_dismiss_ms: int,
      primary_action: str,
      secondary_action: str,
      primary_destination: str,
      secondary_destination: str,
      profile_pool: str,
      profile_seed: int,
      profile_strategy: str,
      wait_after_launch_sec: float,
  ) -> "HelperInterruptionPerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]
    parsed_profile_pool = _parse_profile_pool(profile_pool)
    normalized_profile_strategy = profile_strategy.strip().lower() or "cycle"
    if normalized_profile_strategy not in VALID_HELPER_INTERRUPTION_PROFILE_STRATEGIES:
      raise ValueError(
          "profile_strategy must be one of "
          + ", ".join(sorted(VALID_HELPER_INTERRUPTION_PROFILE_STRATEGIES))
      )
    return cls(
        enabled=enabled,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        kind=kind.strip().lower(),
        surface_style=surface_style.strip().lower(),
        app_name=app_name,
        title=title,
        message=message,
        primary_button=primary_button,
        secondary_button=secondary_button,
        blocking=blocking,
        auto_dismiss_ms=max(int(auto_dismiss_ms), 0),
        primary_action=primary_action,
        secondary_action=secondary_action,
        primary_destination=primary_destination,
        secondary_destination=secondary_destination,
        profile_pool=parsed_profile_pool,
        profile_seed=profile_seed,
        profile_strategy=normalized_profile_strategy,
        wait_after_launch_sec=max(wait_after_launch_sec, 0.0),
    )


class HelperInterruptionPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that launches the helper app at configured steps."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: HelperInterruptionPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_metadata: dict[str, object] | None = None
    self._profile_rng = random.Random(config.profile_seed)
    self._profile_cycle: list[str] = []

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_metadata = None
    self._profile_rng = random.Random(self._config.profile_seed)
    self._profile_cycle = []
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
    profile_name = self._next_profile_name()
    spec = _build_interruption_spec(self._config, profile_name=profile_name)
    show_helper_interruption(spec, self._base_env.controller)
    if self._config.wait_after_launch_sec > 0:
      time.sleep(self._config.wait_after_launch_sec)
    self._last_metadata = {
        "active": True,
        "trigger_step": current_step,
        "profile_name": profile_name or "",
        "kind": spec.kind,
        "surface_style": spec.surface_style,
        "app_name": spec.app_name,
        "title": spec.title,
        "blocking": spec.blocking,
        "auto_dismiss_ms": spec.auto_dismiss_ms,
        "primary_action": spec.primary_action,
        "secondary_action": spec.secondary_action,
        "primary_destination": spec.primary_destination,
        "secondary_destination": spec.secondary_destination,
        "instance_id": spec.instance_id,
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

  def _next_profile_name(self) -> str | None:
    if not self._config.profile_pool:
      return None
    if self._config.profile_strategy == "random":
      return self._profile_rng.choice(self._config.profile_pool)
    if not self._profile_cycle:
      self._profile_cycle = list(self._config.profile_pool)
      self._profile_rng.shuffle(self._profile_cycle)
    return self._profile_cycle.pop(0)

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_helper_interruption"] = dict(self._last_metadata or {})
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )


def _parse_profile_pool(profile_pool: str) -> tuple[str, ...]:
  parsed_profiles = []
  for raw_name in profile_pool.split(","):
    name = raw_name.strip()
    if not name:
      continue
    if name not in _HELPER_INTERRUPTION_PROFILES:
      raise ValueError(
          f"Unknown helper interruption profile: {name!r}. Available profiles: "
          + ", ".join(sorted(_HELPER_INTERRUPTION_PROFILES))
      )
    parsed_profiles.append(name)
  return tuple(parsed_profiles)


def _build_interruption_spec(
    config: HelperInterruptionPerturbationConfig,
    *,
    profile_name: str | None,
) -> HelperInterruptionSpec:
  if profile_name:
    profile_kwargs = dict(_HELPER_INTERRUPTION_PROFILES[profile_name])
    return HelperInterruptionSpec(**profile_kwargs)
  return HelperInterruptionSpec(
      kind=config.kind,
      surface_style=config.surface_style,
      title=config.title,
      message=config.message,
      app_name=config.app_name,
      primary_button=config.primary_button,
      secondary_button=config.secondary_button,
      blocking=config.blocking,
      auto_dismiss_ms=config.auto_dismiss_ms,
      primary_action=config.primary_action,
      secondary_action=config.secondary_action,
      primary_destination=config.primary_destination,
      secondary_destination=config.secondary_destination,
  )
