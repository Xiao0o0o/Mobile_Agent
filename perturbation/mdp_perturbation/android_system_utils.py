"""Shared ADB helpers for real-emulator perturbations."""

from __future__ import annotations

import re
from typing import Any

from android_world.env import adb_utils

_VALID_ACTIVATION_MODES = frozenset({"on_reset", "on_steps"})
_ACTIVATION_MODE_ALIASES = {
    "reset": "on_reset",
    "persistent": "on_reset",
    "step": "on_steps",
    "steps": "on_steps",
}


def _decode_response_output(response) -> str:
  return response.generic.output.decode("utf-8", errors="ignore").strip()


def issue_shell_command(controller, *args: str):
  return adb_utils.issue_generic_request(["shell", *args], controller)


def read_system_setting(controller, namespace: str, key: str) -> str | None:
  output = _decode_response_output(
      issue_shell_command(controller, "settings", "get", namespace, key)
  )
  if output in ("", "null"):
    return None
  return output


def put_system_setting(
    controller,
    namespace: str,
    key: str,
    value: str,
) -> None:
  issue_shell_command(controller, "settings", "put", namespace, key, value)


def delete_system_setting(controller, namespace: str, key: str) -> None:
  issue_shell_command(controller, "settings", "delete", namespace, key)


def read_font_scale(controller) -> tuple[str | None, float]:
  raw_value = read_system_setting(controller, "system", "font_scale")
  if raw_value is None:
    return None, 1.0
  try:
    return raw_value, float(raw_value)
  except ValueError:
    return raw_value, 1.0


def parse_wm_density(output: str) -> dict[str, int | None]:
  physical_match = re.search(r"Physical density:\s*(\d+)", output)
  override_match = re.search(r"Override density:\s*(\d+)", output)
  if not physical_match:
    raise RuntimeError(f"Unable to parse wm density output: {output!r}")
  physical_density = int(physical_match.group(1))
  override_density = int(override_match.group(1)) if override_match else None
  return {
      "physical_density": physical_density,
      "override_density": override_density,
      "effective_density": override_density or physical_density,
  }


def read_wm_density(controller) -> dict[str, int | None]:
  output = _decode_response_output(issue_shell_command(controller, "wm", "density"))
  return parse_wm_density(output)


def set_wm_density(controller, density: int) -> None:
  issue_shell_command(controller, "wm", "density", str(int(density)))


def reset_wm_density(controller) -> None:
  issue_shell_command(controller, "wm", "density", "reset")


def parse_wm_size(output: str) -> dict[str, tuple[int, int] | None]:
  physical_match = re.search(r"Physical size:\s*(\d+)x(\d+)", output)
  override_match = re.search(r"Override size:\s*(\d+)x(\d+)", output)
  if not physical_match:
    raise RuntimeError(f"Unable to parse wm size output: {output!r}")
  physical_size = (int(physical_match.group(1)), int(physical_match.group(2)))
  override_size = (
      (int(override_match.group(1)), int(override_match.group(2)))
      if override_match
      else None
  )
  return {
      "physical_size": physical_size,
      "override_size": override_size,
      "effective_size": override_size or physical_size,
  }


def read_wm_size(controller) -> dict[str, tuple[int, int] | None]:
  output = _decode_response_output(issue_shell_command(controller, "wm", "size"))
  return parse_wm_size(output)


def set_wm_size(controller, width: int, height: int) -> None:
  issue_shell_command(controller, "wm", "size", f"{int(width)}x{int(height)}")


def reset_wm_size(controller) -> None:
  issue_shell_command(controller, "wm", "size", "reset")


def restore_optional_system_setting(
    controller,
    namespace: str,
    key: str,
    raw_value: str | None,
) -> None:
  if raw_value is None:
    delete_system_setting(controller, namespace, key)
  else:
    put_system_setting(controller, namespace, key, raw_value)


def clamp_int(value: float, minimum: int) -> int:
  return max(minimum, int(round(value)))


def normalize_activation_mode(activation_mode: str) -> str:
  normalized_mode = activation_mode.strip().lower() or "on_reset"
  normalized_mode = _ACTIVATION_MODE_ALIASES.get(
      normalized_mode,
      normalized_mode,
  )
  if normalized_mode not in _VALID_ACTIVATION_MODES:
    raise ValueError(
        "activation_mode must be one of "
        f"{sorted(_VALID_ACTIVATION_MODES)}; got {activation_mode!r}."
    )
  return normalized_mode


def dict_without_none(payload: dict[str, Any]) -> dict[str, Any]:
  return {key: value for key, value in payload.items() if value is not None}
