"""Execution-delay perturbation for AndroidWorld."""

from __future__ import annotations

import dataclasses
from typing import Iterable

from android_world.env import interface
import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageEnhance
from PIL import ImageFont


@dataclasses.dataclass(frozen=True)
class ExecutionDelayPerturbationConfig:
  """Configuration for delayed state transitions."""

  enabled: bool = False
  trigger_steps: tuple[int, ...] = (3,)
  delay_steps: int = 2
  mode: str = "loading"
  block_actions_while_pending: bool = True
  loading_text: str = "Loading..."
  frozen_title: str = "App isn't responding"
  frozen_message: str = "The app is taking longer than usual to respond."

  @classmethod
  def from_flag_string(
      cls,
      *,
      enabled: bool,
      trigger_steps: str,
      delay_steps: int,
      mode: str,
      block_actions_while_pending: bool,
      loading_text: str,
      frozen_title: str,
      frozen_message: str,
  ) -> "ExecutionDelayPerturbationConfig":
    parsed_steps = []
    for raw_step in trigger_steps.split(","):
      raw_step = raw_step.strip()
      if raw_step:
        parsed_steps.append(int(raw_step))
    if not parsed_steps:
      parsed_steps = [3]
    if mode not in ("loading", "frozen", "skeleton"):
      raise ValueError("mode must be one of 'loading', 'frozen', or 'skeleton'")
    return cls(
        enabled=enabled,
        trigger_steps=tuple(sorted(set(step for step in parsed_steps if step >= 0))),
        delay_steps=max(delay_steps, 1),
        mode=mode,
        block_actions_while_pending=block_actions_while_pending,
        loading_text=loading_text,
        frozen_title=frozen_title,
        frozen_message=frozen_message,
    )


class ExecutionDelayPerturbationEnv(interface.AsyncEnv):
  """AsyncEnv wrapper that delays visible state updates."""

  interaction_cache = ""

  def __init__(
      self,
      base_env: interface.AsyncEnv,
      config: ExecutionDelayPerturbationConfig,
  ):
    self._base_env = base_env
    self._config = config
    self._executed_action_count = 0
    self._activated_steps: set[int] = set()
    self._last_base_state: interface.State | None = None
    self._pending_reference_state: interface.State | None = None
    self._pending_remaining = 0

  def reset(self, go_home: bool = False) -> interface.State:
    self._executed_action_count = 0
    self._activated_steps.clear()
    self._pending_reference_state = None
    self._pending_remaining = 0
    state = self._base_env.reset(go_home=go_home)
    self._last_base_state = state
    return state

  def get_state(self, wait_to_stabilize: bool = False) -> interface.State:
    base_state = self._base_env.get_state(wait_to_stabilize=wait_to_stabilize)
    self._last_base_state = base_state
    if self._pending_remaining <= 0 or self._pending_reference_state is None:
      return base_state

    delayed_state = self._decorate_pending_state(self._pending_reference_state)
    self._pending_remaining -= 1
    if self._pending_remaining <= 0:
      self._pending_reference_state = None
    return delayed_state

  def execute_action(self, action) -> None:
    action_type = getattr(action, "action_type", None)
    if action_type in ("answer", "status"):
      self._base_env.execute_action(action)
      return

    self._executed_action_count += 1

    if self._pending_remaining > 0 and self._config.block_actions_while_pending:
      return

    if self._last_base_state is None:
      self._last_base_state = self._base_env.get_state(wait_to_stabilize=False)

    self._base_env.execute_action(action)

    current_step = self._executed_action_count
    if current_step in self._config.trigger_steps and current_step not in self._activated_steps:
      self._pending_reference_state = self._last_base_state
      self._pending_remaining = self._config.delay_steps
      self._activated_steps.add(current_step)

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

  def _decorate_pending_state(self, state: interface.State) -> interface.State:
    if self._config.mode == "frozen":
      pixels = _render_frozen_overlay(
          state.pixels,
          title=self._config.frozen_title,
          message=self._config.frozen_message,
      )
    elif self._config.mode == "skeleton":
      pixels = _render_skeleton_overlay(
          state.pixels,
          label=self._config.loading_text,
      )
    else:
      pixels = _render_loading_overlay(
          state.pixels,
          label=self._config.loading_text,
      )
    auxiliaries = dict(state.auxiliaries or {})
    auxiliaries["mdp_execution_delay"] = {
        "active": True,
        "mode": self._config.mode,
        "remaining_steps": self._pending_remaining,
        "block_actions_while_pending": self._config.block_actions_while_pending,
    }
    return interface.State(
        pixels=pixels,
        forest=state.forest,
        ui_elements=state.ui_elements,
        auxiliaries=auxiliaries,
    )


def _render_loading_overlay(pixels: np.ndarray, label: str) -> np.ndarray:
  image = Image.fromarray(pixels).convert("RGBA")
  base = ImageEnhance.Brightness(image).enhance(0.72)
  overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(overlay)
  width, height = image.size

  bar_height = max(int(height * 0.008), 12)
  draw.rectangle((0, 0, int(width * 0.72), bar_height), fill=(59, 130, 246, 255))

  card_width = min(int(width * 0.58), 760)
  card_height = min(int(height * 0.18), 320)
  left = int((width - card_width) / 2)
  top = int((height - card_height) / 2)
  card_bbox = (left, top, left + card_width, top + card_height)
  draw.rounded_rectangle(
      card_bbox,
      radius=28,
      fill=(248, 250, 252, 245),
      outline=(203, 213, 225, 255),
      width=2,
  )

  spinner_radius = max(int(card_height * 0.14), 22)
  spinner_center = (left + 62, top + int(card_height / 2))
  draw.ellipse(
      (
          spinner_center[0] - spinner_radius,
          spinner_center[1] - spinner_radius,
          spinner_center[0] + spinner_radius,
          spinner_center[1] + spinner_radius,
      ),
      outline=(59, 130, 246, 255),
      width=8,
  )
  draw.arc(
      (
          spinner_center[0] - spinner_radius,
          spinner_center[1] - spinner_radius,
          spinner_center[0] + spinner_radius,
          spinner_center[1] + spinner_radius,
      ),
      start=300,
      end=70,
      fill=(14, 165, 233, 255),
      width=8,
  )

  title_font = _load_font(max(int(card_width * 0.055), 30), bold=True)
  body_font = _load_font(max(int(card_width * 0.040), 24), bold=False)
  text_left = left + 124
  title_y = top + int(card_height * 0.30)
  draw.text(
      (text_left, title_y),
      label,
      fill=(15, 23, 42, 255),
      font=title_font,
  )
  draw.text(
      (text_left, title_y + 54),
      "Please wait while the page finishes updating.",
      fill=(71, 85, 105, 255),
      font=body_font,
  )
  composited = Image.alpha_composite(base, overlay)
  return np.asarray(composited.convert("RGB"))


def _render_frozen_overlay(
    pixels: np.ndarray,
    title: str,
    message: str,
) -> np.ndarray:
  image = Image.fromarray(pixels).convert("RGBA")
  base = ImageEnhance.Brightness(image).enhance(0.48)
  overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(overlay)
  width, height = image.size
  draw.rectangle((0, 0, width, height), fill=(15, 23, 42, 92))

  card_width = min(int(width * 0.74), 820)
  card_height = min(int(height * 0.22), 420)
  left = int((width - card_width) / 2)
  top = int((height - card_height) / 2)
  card_bbox = (left, top, left + card_width, top + card_height)
  draw.rounded_rectangle(
      card_bbox,
      radius=30,
      fill=(255, 255, 255, 255),
      outline=(226, 232, 240, 255),
      width=2,
  )

  title_font = _load_font(max(int(card_width * 0.052), 30), bold=True)
  body_font = _load_font(max(int(card_width * 0.038), 22), bold=False)
  button_font = _load_font(max(int(card_width * 0.038), 22), bold=True)

  text_left = left + 34
  text_width = card_width - 68
  current_y = top + 34
  for line in _wrap_text(draw, title, title_font, text_width):
    draw.text((text_left, current_y), line, fill=(15, 23, 42, 255), font=title_font)
    current_y += _line_height(draw, title_font, line, 10)
  for line in _wrap_text(draw, message, body_font, text_width):
    draw.text((text_left, current_y), line, fill=(71, 85, 105, 255), font=body_font)
    current_y += _line_height(draw, body_font, line, 8)

  button_height = max(int(card_height * 0.22), 74)
  button_width = min(int(card_width * 0.34), 240)
  button_bbox = (
      left + card_width - button_width - 28,
      top + card_height - button_height - 22,
      left + card_width - 28,
      top + card_height - 22,
  )
  draw.rounded_rectangle(
      button_bbox,
      radius=18,
      fill=(239, 246, 255, 255),
      outline=(59, 130, 246, 255),
      width=2,
  )
  draw.text(
      (int((button_bbox[0] + button_bbox[2]) / 2), int((button_bbox[1] + button_bbox[3]) / 2)),
      "Wait",
      fill=(37, 99, 235, 255),
      font=button_font,
      anchor="mm",
  )

  composited = Image.alpha_composite(base, overlay)
  return np.asarray(composited.convert("RGB"))


def _render_skeleton_overlay(pixels: np.ndarray, label: str) -> np.ndarray:
  image = Image.fromarray(pixels).convert("RGBA")
  base = ImageEnhance.Brightness(image).enhance(0.84)
  overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(overlay)
  width, height = image.size

  top_bar_height = max(int(height * 0.07), 96)
  draw.rectangle((0, 0, width, top_bar_height), fill=(248, 250, 252, 235))
  draw.rounded_rectangle(
      (24, int(top_bar_height * 0.28), int(width * 0.54), int(top_bar_height * 0.72)),
      radius=18,
      fill=(226, 232, 240, 255),
  )
  draw.rounded_rectangle(
      (int(width * 0.82), int(top_bar_height * 0.30), width - 24, int(top_bar_height * 0.70)),
      radius=18,
      fill=(226, 232, 240, 255),
  )

  gutter = max(int(width * 0.05), 24)
  card_top = top_bar_height + 26
  line_gap = max(int(height * 0.022), 24)
  placeholder_fill = (226, 232, 240, 255)
  highlight_fill = (241, 245, 249, 255)

  for row_index in range(5):
    row_top = card_top + row_index * (line_gap + int(height * 0.08))
    if row_top >= height - 120:
      break
    draw.rounded_rectangle(
        (gutter, row_top, width - gutter, row_top + int(height * 0.065)),
        radius=26,
        fill=highlight_fill,
    )
    draw.rounded_rectangle(
        (
            gutter + 18,
            row_top + 18,
            gutter + int(width * 0.18),
            row_top + 40,
        ),
        radius=12,
        fill=placeholder_fill,
    )
    draw.rounded_rectangle(
        (
            gutter + 18,
            row_top + 58,
            width - gutter - int(width * 0.16),
            row_top + 84,
        ),
        radius=12,
        fill=placeholder_fill,
    )
    draw.rounded_rectangle(
        (
            width - gutter - int(width * 0.18),
            row_top + 20,
            width - gutter - 18,
            row_top + 88,
        ),
        radius=18,
        fill=placeholder_fill,
    )

  footer_height = max(int(height * 0.13), 150)
  draw.rectangle(
      (0, height - footer_height, width, height),
      fill=(255, 255, 255, 224),
  )
  draw.rounded_rectangle(
      (gutter, height - footer_height + 22, width - gutter, height - 28),
      radius=26,
      fill=placeholder_fill,
  )

  title_font = _load_font(max(int(width * 0.028), 26), bold=True)
  body_font = _load_font(max(int(width * 0.020), 18), bold=False)
  draw.text(
      (gutter, top_bar_height + 6),
      label or "Loading content...",
      fill=(15, 23, 42, 255),
      font=title_font,
  )
  draw.text(
      (gutter, top_bar_height + 44),
      "Some interface blocks are still rendering.",
      fill=(71, 85, 105, 255),
      font=body_font,
  )

  composited = Image.alpha_composite(base, overlay)
  return np.asarray(composited.convert("RGB"))


def _line_height(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    sample_text: str,
    extra_padding: int,
) -> int:
  bbox = draw.textbbox((0, 0), sample_text or "Ag", font=font)
  return (bbox[3] - bbox[1]) + extra_padding


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
  words = text.split()
  if not words:
    return [text]
  lines: list[str] = []
  current = words[0]
  for word in words[1:]:
    candidate = f"{current} {word}"
    bbox = draw.textbbox((0, 0), candidate, font=font)
    if (bbox[2] - bbox[0]) <= max_width:
      current = candidate
    else:
      lines.append(current)
      current = word
  lines.append(current)
  return lines


def _load_font(preferred_size: int, bold: bool) -> ImageFont.ImageFont:
  candidate_paths: Iterable[str]
  if bold:
    candidate_paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    )
  else:
    candidate_paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    )
  for path in candidate_paths:
    try:
      return ImageFont.truetype(path, preferred_size)
    except OSError:
      continue
  return ImageFont.load_default()
