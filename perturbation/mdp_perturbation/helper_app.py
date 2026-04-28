"""Utilities for launching the perturbation helper app."""

from __future__ import annotations

import dataclasses
import uuid

from android_world.env import adb_utils


ACTION_SHOW_INTERRUPTION = (
    "com.google.androidenv.perturbationhelper.SHOW_INTERRUPTION"
)

VALID_INTERRUPTION_KINDS = frozenset({"popup", "ad", "update", "notification"})
VALID_SURFACE_STYLES = frozenset(
    {"dialog", "bottom_sheet", "interstitial", "banner"}
)
VALID_BUTTON_ACTIONS = frozenset({"dismiss", "open_destination"})


@dataclasses.dataclass(frozen=True)
class HelperInterruptionSpec:
  """Description of a helper-app interruption."""

  kind: str = "popup"
  surface_style: str = ""
  title: str = ""
  message: str = ""
  app_name: str = ""
  primary_button: str = ""
  secondary_button: str = ""
  blocking: bool = True
  auto_dismiss_ms: int = 0
  primary_action: str = ""
  secondary_action: str = ""
  primary_destination: str = ""
  secondary_destination: str = ""
  instance_id: str = dataclasses.field(
      default_factory=lambda: uuid.uuid4().hex[:12]
  )

  def __post_init__(self):
    normalized_kind = self.kind.strip().lower()
    if normalized_kind not in VALID_INTERRUPTION_KINDS:
      raise ValueError(
          f"Unsupported helper interruption kind: {self.kind!r}. "
          f"Expected one of {sorted(VALID_INTERRUPTION_KINDS)}."
      )
    object.__setattr__(self, "kind", normalized_kind)
    normalized_surface_style = self.surface_style.strip().lower()
    if not normalized_surface_style:
      normalized_surface_style = _default_surface_style_for_kind(normalized_kind)
    if normalized_surface_style not in VALID_SURFACE_STYLES:
      raise ValueError(
          f"Unsupported helper surface style: {self.surface_style!r}. "
          f"Expected one of {sorted(VALID_SURFACE_STYLES)}."
      )
    object.__setattr__(self, "surface_style", normalized_surface_style)
    object.__setattr__(self, "auto_dismiss_ms", max(int(self.auto_dismiss_ms), 0))
    raw_primary_action = self.primary_action.strip().lower()
    raw_secondary_action = self.secondary_action.strip().lower()
    if raw_primary_action and raw_primary_action not in VALID_BUTTON_ACTIONS:
      raise ValueError(
          f"Unsupported primary action: {self.primary_action!r}. "
          f"Expected one of {sorted(VALID_BUTTON_ACTIONS)}."
      )
    if raw_secondary_action and raw_secondary_action not in VALID_BUTTON_ACTIONS:
      raise ValueError(
          f"Unsupported secondary action: {self.secondary_action!r}. "
          f"Expected one of {sorted(VALID_BUTTON_ACTIONS)}."
      )

    normalized_primary_destination = self.primary_destination.strip()
    if not normalized_primary_destination:
      normalized_primary_destination = _infer_destination(self, is_primary=True)
    normalized_secondary_destination = self.secondary_destination.strip()
    if not normalized_secondary_destination:
      normalized_secondary_destination = _infer_destination(self, is_primary=False)

    normalized_primary_action = _resolve_action(
        raw_primary_action, normalized_primary_destination
    )
    normalized_secondary_action = _resolve_action(
        raw_secondary_action, normalized_secondary_destination
    )
    if normalized_primary_action != "open_destination":
      normalized_primary_destination = ""
    if normalized_secondary_action != "open_destination":
      normalized_secondary_destination = ""

    object.__setattr__(self, "primary_action", normalized_primary_action)
    object.__setattr__(self, "secondary_action", normalized_secondary_action)
    object.__setattr__(self, "primary_destination", normalized_primary_destination)
    object.__setattr__(self, "secondary_destination", normalized_secondary_destination)

  def to_intent_extras(self) -> dict[str, str | bool | tuple[str, int]]:
    extras: dict[str, str | bool | tuple[str, int]] = {
        "kind": self.kind,
        "surface_style": self.surface_style,
        "blocking": self.blocking,
        "auto_dismiss_ms": ("long", self.auto_dismiss_ms),
        "primary_action": self.primary_action,
        "secondary_action": self.secondary_action,
        "instance_id": self.instance_id,
    }
    if self.title:
      extras["title"] = self.title
    if self.message:
      extras["message"] = self.message
    if self.app_name:
      extras["app_name"] = self.app_name
    if self.primary_button:
      extras["primary_button"] = self.primary_button
    if self.secondary_button:
      extras["secondary_button"] = self.secondary_button
    if self.primary_destination:
      extras["primary_destination"] = self.primary_destination
    if self.secondary_destination:
      extras["secondary_destination"] = self.secondary_destination
    return extras


def _default_surface_style_for_kind(kind: str) -> str:
  if kind == "notification":
    return "banner"
  if kind == "ad":
    return "interstitial"
  return "dialog"


def _resolve_action(raw_action: str, destination: str) -> str:
  if not raw_action:
    return "open_destination" if destination else "dismiss"
  if raw_action == "open_destination" and destination:
    return raw_action
  return "dismiss"


def _normalize_text(*parts: str) -> str:
  return " ".join(part.strip().lower() for part in parts if part).strip()


def _contains_any(text: str, *tokens: str) -> bool:
  return any(token in text for token in tokens)


def _infer_destination(spec: HelperInterruptionSpec, *, is_primary: bool) -> str:
  button_text = _normalize_text(
      spec.primary_button if is_primary else spec.secondary_button
  )
  content = _normalize_text(
      spec.app_name,
      spec.title,
      spec.message,
      spec.primary_button,
      spec.secondary_button,
  )

  if (
      not is_primary
      and _contains_any(
          content,
          "privacy choices",
          "analytics",
          "personalized content",
          "cookies",
      )
      and _contains_any(button_text, "manage", "options", "choices", "settings")
  ):
    return "privacy_options"

  if _contains_any(
      content,
      "rate this app",
      "enjoying",
      "how was your experience",
      "tell us what is working well",
  ) or _contains_any(button_text, "rate", "review", "stars", "submit"):
    return "rating_flow" if is_primary else ""

  if spec.kind == "update" or _contains_any(
      content,
      "update available",
      "new version",
      "security fixes",
      "system update",
      "what's new",
      "bug fixes",
  ):
    if not is_primary and not _contains_any(
        button_text, "view", "details", "open", "learn more", "all updates"
    ):
      return ""
    if _contains_any(
        content,
        "system updater",
        "android system",
        "system update",
        "security patch",
        "restart required",
    ):
      return "system_update_settings"
    return "app_store_update"

  if spec.kind == "notification":
    if _contains_any(
        content, "driver", "delivery", "package", "parcel", "track"
    ) or _contains_any(button_text, "track", "map"):
      return "delivery_tracking" if is_primary else ""
    return "message_thread" if is_primary else ""

  if _contains_any(
      content,
      "verify this action",
      "protected system setting",
      "security center",
      "risk summary",
      "protected action review",
  ):
    if is_primary or _contains_any(button_text, "continue", "approve", "review"):
      return "security_center"
    return ""

  if _contains_any(
      content,
      "allow notifications",
      "notification permissions",
      "send alerts",
      "alerts while you use this app",
  ) and _contains_any(button_text, "allow", "continue", "open", "settings"):
    return "notification_settings"

  if spec.kind == "ad" or _contains_any(
      content, "flash sale", "travel gear", "shop", "deals", "cart", "prime badge"
  ):
    if _contains_any(button_text, "shop", "cart", "deal", "buy", "open"):
      return "shopping_amazon"
    if is_primary and _contains_any(button_text, "install", "download", "get"):
      return "app_store_update"

  return ""


def show_helper_interruption(spec: HelperInterruptionSpec, env, timeout_sec: int = 5):
  """Launches the helper app with the given interruption spec."""

  return adb_utils.send_android_intent(
      command="start",
      action=ACTION_SHOW_INTERRUPTION,
      env=env,
      extras=spec.to_intent_extras(),
      timeout_sec=timeout_sec,
  )
