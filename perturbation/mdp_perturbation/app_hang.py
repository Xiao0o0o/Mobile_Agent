"""App-hang perturbation that requires recovery or restart."""

from __future__ import annotations

import dataclasses
import time

from android_world.env import adb_utils
from android_world.env import interface
from mdp_perturbation.android_system_utils import issue_shell_command
from mdp_perturbation.execution_delay import _line_height
from mdp_perturbation.execution_delay import _load_font
from mdp_perturbation.execution_delay import _wrap_text
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageEnhance


@dataclasses.dataclass(frozen=True)
class AppHangPerturbationConfig:
  """Configuration for a persistent app hang requiring recovery."""

  enabled: bool = False
  trigger_steps: tuple[int, ...] = (3,)
  title: str = "App isn't responding"
  message: str = "This app stopped responding. Restart it to continue."
  restart_button: str = "Restart app"
  close_button: str = "Close app"
  settle_time_sec: float = 1.0
  allow_home_recovery: bool = True
  allow_open_app_recovery: bool = True
  close_goes_home: bool = True

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      trigger_steps: str,
      title: str,
      message: str,
      restart_button: str,
      close_button: str,
      settle_time_sec: float,
      allow_home_recovery: bool,
      allow_open_app_recovery: bool,
      close_goes_home: bool,
  ) -> "AppHangPerturbationConfig":
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
        title=title,
        message=message,
        restart_button=restart_button,
        close_button=close_button,
        settle_time_sec=max(settle_time_sec, 0.0),
        allow_home_recovery=allow_home_recovery,
        allow_open_app_recovery=allow_open_app_recovery,
        close_goes_home=close_goes_home,
    )


class AppHangPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that freezes an app until the agent restarts it."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: AppHangPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_base_state: interface.State | None = None
    self._last_metadata: dict[str, object] | None = None
    self._hung_reference_state: interface.State | None = None
    self._hung_package_name = ""
    self._hung_activity_name = ""

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._last_metadata = None
    self._hung_reference_state = None
    self._hung_package_name = ""
    self._hung_activity_name = ""
    state = self._base_env.reset(go_home=go_home)
    self._last_base_state = state
    return self._decorate_state(state)

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    base_state = self._base_env.get_state(wait_to_stabilize=wait_to_stabilize)
    self._last_base_state = base_state
    if self._hung_reference_state is None:
      return self._decorate_state(base_state)
    return self._decorate_state(
        interface.State(
            pixels=_render_hang_overlay(
                self._hung_reference_state.pixels,
                title=self._config.title,
                message=self._config.message,
                restart_button=self._config.restart_button,
                close_button=self._config.close_button,
            ),
            forest=self._hung_reference_state.forest,
            ui_elements=self._hung_reference_state.ui_elements,
            auxiliaries=self._hung_reference_state.auxiliaries,
        )
    )

  def execute_action(self, action) -> None:
    action_type = getattr(action, "action_type", None)
    if action_type in ("answer", "status"):
      self._base_env.execute_action(action)
      return

    self._executed_action_count += 1

    if self._hung_reference_state is not None:
      if self._handle_recovery_action(action):
        return
      self._last_metadata = {
          "active": True,
          "hang_active": True,
          "trigger_step": self._last_metadata.get("trigger_step") if self._last_metadata else None,
          "hung_activity": self._hung_activity_name,
          "hung_package": self._hung_package_name,
          "ignored_action_type": action_type,
      }
      return

    if self._last_base_state is None:
      self._last_base_state = self._base_env.get_state(wait_to_stabilize=False)

    current_step = self._executed_action_count
    if (
        self._config.enabled
        and current_step in self._config.trigger_steps
        and current_step not in self._activated_steps
    ):
      self._activated_steps.add(current_step)
      self._activate_hang(trigger_step=current_step)
      return

    self._base_env.execute_action(action)

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

  def _activate_hang(self, trigger_step: int) -> None:
    self._hung_reference_state = self._last_base_state
    self._hung_activity_name = self._base_env.foreground_activity_name or ""
    self._hung_package_name = ""
    if self._hung_activity_name and "/" in self._hung_activity_name:
      self._hung_package_name = adb_utils.extract_package_name(self._hung_activity_name)
    self._last_metadata = {
        "active": True,
        "hang_active": True,
        "trigger_step": trigger_step,
        "hung_activity": self._hung_activity_name,
        "hung_package": self._hung_package_name,
        "recovery_hint": "restart_or_home",
    }

  def _handle_recovery_action(self, action) -> bool:
    action_type = getattr(action, "action_type", None)
    if action_type == "click" and self._hung_reference_state is not None:
      button = _which_hang_button(
          self._hung_reference_state.pixels.shape[1],
          self._hung_reference_state.pixels.shape[0],
          getattr(action, "x", None),
          getattr(action, "y", None),
      )
      if button == "restart":
        self._restart_hung_app("overlay_restart_button")
        return True
      if button == "close":
        self._close_hung_app("overlay_close_button")
        return True

    if action_type == "navigate_home" and self._config.allow_home_recovery:
      self._base_env.execute_action(action)
      self._clear_hang("navigate_home")
      return True

    if action_type == "open_app" and self._config.allow_open_app_recovery:
      self._base_env.execute_action(action)
      self._clear_hang("open_app")
      return True

    return False

  def _restart_hung_app(self, recovery_action: str) -> None:
    if self._hung_package_name:
      issue_shell_command(self._base_env.controller, "am", "force-stop", self._hung_package_name)
      issue_shell_command(
          self._base_env.controller,
          "monkey",
          "-p",
          self._hung_package_name,
          "-c",
          "android.intent.category.LAUNCHER",
          "1",
      )
    elif self._config.allow_home_recovery:
      adb_utils.press_home_button(self._base_env.controller)
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    self._clear_hang(recovery_action)

  def _close_hung_app(self, recovery_action: str) -> None:
    if self._hung_package_name:
      issue_shell_command(self._base_env.controller, "am", "force-stop", self._hung_package_name)
    if self._config.close_goes_home:
      adb_utils.press_home_button(self._base_env.controller)
    if self._config.settle_time_sec > 0:
      time.sleep(self._config.settle_time_sec)
    self._clear_hang(recovery_action)

  def _clear_hang(self, recovery_action: str) -> None:
    self._hung_reference_state = None
    self._last_metadata = {
        "active": True,
        "hang_active": False,
        "recovered": True,
        "recovery_action": recovery_action,
        "hung_activity": self._hung_activity_name,
        "hung_package": self._hung_package_name,
    }
    self._hung_package_name = ""
    self._hung_activity_name = ""

  def _decorate_state(self, state: interface.State) -> interface.State:
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_app_hang"] = dict(self._last_metadata or {})
    return interface.State(
        pixels=state.pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )


def _which_hang_button(
    width: int,
    height: int,
    x: int | None,
    y: int | None,
) -> str | None:
  if x is None or y is None:
    return None
  left = int((width - min(int(width * 0.78), 860)) / 2)
  top = int((height - min(int(height * 0.26), 480)) / 2)
  card_width = min(int(width * 0.78), 860)
  card_height = min(int(height * 0.26), 480)
  button_height = max(int(card_height * 0.21), 72)
  button_width = min(int(card_width * 0.30), 250)
  close_bbox = (
      left + card_width - button_width - 28,
      top + card_height - button_height - 24,
      left + card_width - 28,
      top + card_height - 24,
  )
  restart_bbox = (
      close_bbox[0] - button_width - 18,
      close_bbox[1],
      close_bbox[0] - 18,
      close_bbox[3],
  )
  if restart_bbox[0] <= x <= restart_bbox[2] and restart_bbox[1] <= y <= restart_bbox[3]:
    return "restart"
  if close_bbox[0] <= x <= close_bbox[2] and close_bbox[1] <= y <= close_bbox[3]:
    return "close"
  return None


def _render_hang_overlay(
    pixels: np.ndarray,
    title: str,
    message: str,
    restart_button: str,
    close_button: str,
) -> np.ndarray:
  image = Image.fromarray(pixels).convert("RGBA")
  base = ImageEnhance.Brightness(image).enhance(0.42)
  overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(overlay)
  width, height = image.size
  draw.rectangle((0, 0, width, height), fill=(15, 23, 42, 128))

  card_width = min(int(width * 0.78), 860)
  card_height = min(int(height * 0.26), 480)
  left = int((width - card_width) / 2)
  top = int((height - card_height) / 2)
  draw.rounded_rectangle(
      (left, top, left + card_width, top + card_height),
      radius=30,
      fill=(255, 255, 255, 255),
      outline=(226, 232, 240, 255),
      width=2,
  )

  icon_radius = max(int(card_height * 0.11), 26)
  icon_center = (left + 48, top + 46)
  draw.ellipse(
      (
          icon_center[0] - icon_radius,
          icon_center[1] - icon_radius,
          icon_center[0] + icon_radius,
          icon_center[1] + icon_radius,
      ),
      fill=(254, 226, 226, 255),
      outline=(239, 68, 68, 255),
      width=3,
  )
  draw.text(
      icon_center,
      "!",
      fill=(220, 38, 38, 255),
      font=_load_font(max(icon_radius + 6, 28), bold=True),
      anchor="mm",
  )

  title_font = _load_font(max(int(card_width * 0.05), 30), bold=True)
  body_font = _load_font(max(int(card_width * 0.036), 22), bold=False)
  button_font = _load_font(max(int(card_width * 0.034), 20), bold=True)
  caption_font = _load_font(max(int(card_width * 0.028), 18), bold=False)

  text_left = left + 96
  text_width = card_width - 128
  current_y = top + 28
  for line in _wrap_text(draw, title, title_font, text_width):
    draw.text((text_left, current_y), line, fill=(15, 23, 42, 255), font=title_font)
    current_y += _line_height(draw, title_font, line, 10)
  for line in _wrap_text(draw, message, body_font, text_width):
    draw.text((text_left, current_y), line, fill=(71, 85, 105, 255), font=body_font)
    current_y += _line_height(draw, body_font, line, 6)

  draw.text(
      (text_left, top + card_height - 118),
      "Tap Restart app or reopen it from Home.",
      fill=(100, 116, 139, 255),
      font=caption_font,
  )

  button_height = max(int(card_height * 0.21), 72)
  button_width = min(int(card_width * 0.30), 250)
  close_bbox = (
      left + card_width - button_width - 28,
      top + card_height - button_height - 24,
      left + card_width - 28,
      top + card_height - 24,
  )
  restart_bbox = (
      close_bbox[0] - button_width - 18,
      close_bbox[1],
      close_bbox[0] - 18,
      close_bbox[3],
  )

  draw.rounded_rectangle(
      restart_bbox,
      radius=18,
      fill=(219, 234, 254, 255),
      outline=(59, 130, 246, 255),
      width=2,
  )
  draw.rounded_rectangle(
      close_bbox,
      radius=18,
      fill=(248, 250, 252, 255),
      outline=(148, 163, 184, 255),
      width=2,
  )
  draw.text(
      ((restart_bbox[0] + restart_bbox[2]) / 2, (restart_bbox[1] + restart_bbox[3]) / 2),
      restart_button,
      fill=(29, 78, 216, 255),
      font=button_font,
      anchor="mm",
  )
  draw.text(
      ((close_bbox[0] + close_bbox[2]) / 2, (close_bbox[1] + close_bbox[3]) / 2),
      close_button,
      fill=(71, 85, 105, 255),
      font=button_font,
      anchor="mm",
  )

  composited = Image.alpha_composite(base, overlay)
  return np.asarray(composited.convert("RGB"))
