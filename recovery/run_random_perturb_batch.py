#!/usr/bin/env python3
"""Batch runner that samples one perturbation profile per task repeat."""

from __future__ import annotations

import random
import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from android_world import registry as task_registry_lib


PY_CMD = sys.executable
SCRIPT_DIR = Path(__file__).resolve().parent
RUN_SCRIPT = str(SCRIPT_DIR / "run_ma3.py")


@dataclass(frozen=True)
class PerturbationProfile:
  name: str
  description: str


def _extract_success_from_log(task: str, log_path: str, return_code: int) -> tuple[float | None, str]:
  try:
    text = Path(log_path).read_text(encoding="utf-8", errors="ignore")
  except OSError:
    return (None, "missing_log")

  if "Task Successful" in text:
    return (1.0, "task_successful_marker")

  row_pattern = re.compile(
      rf"^{re.escape(task)}\s+\d+\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s*$",
      re.MULTILINE,
  )
  row_match = row_pattern.search(text)
  if row_match:
    return (float(row_match.group(2)), "task_summary_table")

  if "Task Failed" in text or "Reached max number of steps" in text:
    return (0.0, "failure_marker")

  if return_code != 0:
    return (0.0, "nonzero_return_code")

  return (None, "unknown")


def _aggregate_success_by_key(
    results: list[dict[str, object]],
    key_name: str,
) -> dict[str, dict[str, float | int]]:
  grouped: dict[str, list[float]] = defaultdict(list)
  for record in results:
    success = record.get("success")
    if success is None:
      continue
    grouped[str(record[key_name])].append(float(success))

  summary: dict[str, dict[str, float | int]] = {}
  for key, values in sorted(grouped.items()):
    count = len(values)
    summary[key] = {
        "num_runs": count,
        "num_successes": int(sum(values)),
        "success_rate": (sum(values) / count) if count else 0.0,
    }
  return summary


def _load_tasks_from_file(path: str) -> list[str]:
  with open(path, "r", encoding="utf-8") as file_obj:
    return [
        line.strip()
        for line in file_obj
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _list_tasks_for_family(family: str) -> list[str]:
  task_registry = task_registry_lib.TaskRegistry()
  return sorted(task_registry.get_registry(family=family).keys())


def _resolve_tasks(args) -> list[str]:
  if args.tasks:
    return [task.strip() for task in args.tasks.split(",") if task.strip()]
  if args.tasks_file:
    return _load_tasks_from_file(args.tasks_file)
  return _list_tasks_for_family(args.suite_family)


def _prepare_session_directories(session_dir_arg: str) -> dict[str, Path]:
  if session_dir_arg:
    session_dir = Path(session_dir_arg).expanduser()
    if not session_dir.is_absolute():
      session_dir = SCRIPT_DIR / session_dir
  else:
    session_dir = SCRIPT_DIR / "random_perturb_runs" / (
        "session_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )

  logs_dir = session_dir / "logs"
  trajs_dir = session_dir / "trajs"
  android_world_runs_dir = session_dir / "android_world_runs"

  for path in (session_dir, logs_dir, trajs_dir, android_world_runs_dir):
    path.mkdir(parents=True, exist_ok=True)

  return {
      "session_dir": session_dir,
      "logs_dir": logs_dir,
      "trajs_dir": trajs_dir,
      "android_world_runs_dir": android_world_runs_dir,
  }


def _build_profiles(include_clean: bool) -> list[PerturbationProfile]:
  profiles = [
      PerturbationProfile("font_size_large", "System font scale is enlarged."),
      PerturbationProfile("font_size_small", "System font scale is reduced."),
      PerturbationProfile(
          "ui_theme_dark",
          "System theme switches to dark mode.",
      ),
      PerturbationProfile(
          "display_size_dpi_compact",
          "System display size and density change to mimic another device.",
      ),
      PerturbationProfile(
          "display_size_dpi_zoomed_out",
          "System display size and density shrink to reveal more content at once.",
      ),
      PerturbationProfile(
          "orientation_landscape",
          "The device stays in landscape for the whole task.",
      ),
      PerturbationProfile(
          "execution_delay_loading",
          "A transition is delayed while a loading overlay blocks progress.",
      ),
      PerturbationProfile(
          "execution_delay_frozen",
          "A transition is delayed behind an app-not-responding style interruption.",
      ),
      PerturbationProfile(
          "partial_loading_skeleton",
          "Delayed transition shows a skeleton screen before full content appears.",
      ),
      PerturbationProfile(
          "app_hang_restart_required",
          "The app stops responding and must be restarted or reopened.",
      ),
      PerturbationProfile(
          "state_reset_home",
          "The foreground app is shut down and the device returns to Home.",
      ),
      PerturbationProfile(
          "bottom_sheet_consent",
          "A blocking bottom-sheet privacy consent interruption appears.",
      ),
      PerturbationProfile(
          "popup_permission",
          "A blocking permission-style popup interrupts the workflow.",
      ),
      PerturbationProfile(
          "popup_security",
          "A blocking security confirmation popup interrupts the workflow.",
      ),
      PerturbationProfile(
          "interstitial_ad",
          "A blocking interstitial ad appears above the current task.",
      ),
      PerturbationProfile(
          "ad_trial_offer",
          "A premium-trial ad with install-style affordances interrupts the task.",
      ),
      PerturbationProfile(
          "rate_dialog",
          "A blocking app-rating dialog interrupts the workflow.",
      ),
      PerturbationProfile(
          "update_system",
          "A system-style update dialog interrupts the current task.",
      ),
      PerturbationProfile(
          "update_app_sheet",
          "A bottom-sheet app update prompt interrupts the current flow.",
      ),
      PerturbationProfile(
          "notification_message",
          "A heads-up message notification appears and can be dismissed or opened.",
      ),
      PerturbationProfile(
          "notification_delivery",
          "A transient delivery alert banner appears above the task.",
      ),
      PerturbationProfile(
          "locale_date_format_us12",
          "System time/date formatting shifts to a US 12-hour presentation.",
      ),
      PerturbationProfile(
          "locale_date_format_eu24",
          "System time/date formatting shifts to a European 24-hour presentation.",
      ),
      PerturbationProfile(
          "action_delay_realistic",
          "Some actions wait a short wall-clock delay before they execute.",
      ),
      PerturbationProfile(
          "action_drop_random",
          "Some agent actions are silently dropped before reaching the device.",
      ),
  ]
  if include_clean:
    return [PerturbationProfile("clean", "No perturbation; clean baseline run.")] + profiles
  return profiles


def _select_profiles(
    profiles: list[PerturbationProfile],
    requested_profiles: str,
) -> list[PerturbationProfile]:
  if not requested_profiles.strip():
    return profiles

  requested_names = [
      name.strip() for name in requested_profiles.split(",") if name.strip()
  ]
  if not requested_names:
    return profiles

  requested_names = [
      "orientation_landscape" if name == "orientation_toggle" else name
      for name in requested_names
  ]

  requested_name_set = set(requested_names)
  available_names = {profile.name for profile in profiles}
  unknown_names = sorted(requested_name_set - available_names)
  if unknown_names:
    raise ValueError(
        "Unknown perturbation profile(s): "
        + ", ".join(unknown_names)
        + ". Available profiles: "
        + ", ".join(sorted(available_names))
    )

  selected_profiles = [
      profile
      for profile in profiles
      if profile.name == "clean" or profile.name in requested_name_set
  ]
  if not selected_profiles:
    raise ValueError("No perturbation profiles selected after filtering.")
  return selected_profiles


def _sample_profiles_for_task(
    rng: random.Random,
    profiles: list[PerturbationProfile],
    repeats: int,
) -> list[PerturbationProfile]:
  if repeats <= 0:
    return []
  if repeats <= len(profiles):
    return rng.sample(profiles, repeats)
  sampled = list(rng.sample(profiles, len(profiles)))
  while len(sampled) < repeats:
    sampled.append(rng.choice(profiles))
  return sampled


def _perturbation_flags(profile_name: str, args: argparse.Namespace) -> list[str]:
  if profile_name == "clean":
    return []
  if profile_name == "font_size_large":
    return [
        "--mdp_font_size_enable=True",
        "--mdp_font_size_activation_mode=on_reset",
        "--mdp_font_size_trigger_steps=1",
        f"--mdp_font_size_scale={args.font_size_large_scale}",
        "--mdp_font_size_settle_time_sec=1.0",
        "--mdp_font_size_restore_on_close=True",
    ]
  if profile_name == "font_size_small":
    return [
        "--mdp_font_size_enable=True",
        "--mdp_font_size_activation_mode=on_reset",
        "--mdp_font_size_trigger_steps=1",
        f"--mdp_font_size_scale={args.font_size_small_scale}",
        "--mdp_font_size_settle_time_sec=1.0",
        "--mdp_font_size_restore_on_close=True",
    ]
  if profile_name == "ui_theme_dark":
    return [
        "--mdp_ui_theme_enable=True",
        "--mdp_ui_theme_activation_mode=on_reset",
        "--mdp_ui_theme_trigger_steps=1",
        "--mdp_ui_theme_mode=dark",
        "--mdp_ui_theme_settle_time_sec=1.0",
        "--mdp_ui_theme_restore_on_close=True",
    ]
  if profile_name == "display_size_dpi_compact":
    return [
        "--mdp_display_size_dpi_enable=True",
        "--mdp_display_size_dpi_activation_mode=on_reset",
        "--mdp_display_size_dpi_trigger_steps=1",
        f"--mdp_display_size_dpi_density_scale={args.display_compact_density_scale}",
        f"--mdp_display_size_dpi_size_scale={args.display_compact_size_scale}",
        "--mdp_display_size_dpi_settle_time_sec=1.2",
        "--mdp_display_size_dpi_restore_on_close=True",
    ]
  if profile_name == "display_size_dpi_zoomed_out":
    return [
        "--mdp_display_size_dpi_enable=True",
        "--mdp_display_size_dpi_activation_mode=on_reset",
        "--mdp_display_size_dpi_trigger_steps=1",
        f"--mdp_display_size_dpi_density_scale={args.display_zoomed_out_density_scale}",
        f"--mdp_display_size_dpi_size_scale={args.display_zoomed_out_size_scale}",
        "--mdp_display_size_dpi_settle_time_sec=1.2",
        "--mdp_display_size_dpi_restore_on_close=True",
    ]
  if profile_name == "orientation_landscape":
    return [
        "--mdp_orientation_enable=True",
        "--mdp_orientation_activation_mode=on_reset",
        "--mdp_orientation_trigger_steps=1",
        f"--mdp_orientation_sequence={args.orientation_profile_sequence}",
        "--mdp_orientation_settle_time_sec=1.2",
        "--mdp_orientation_restore_on_close=True",
    ]
  if profile_name == "execution_delay_loading":
    return [
        "--mdp_execution_delay_enable=True",
        "--mdp_execution_delay_trigger_steps=1",
        "--mdp_execution_delay_steps=2",
        "--mdp_execution_delay_mode=loading",
        "--mdp_execution_delay_block_actions=True",
        "--mdp_execution_delay_loading_text=Loading...",
    ]
  if profile_name == "execution_delay_frozen":
    return [
        "--mdp_execution_delay_enable=True",
        "--mdp_execution_delay_trigger_steps=1",
        "--mdp_execution_delay_steps=2",
        "--mdp_execution_delay_mode=frozen",
        "--mdp_execution_delay_block_actions=True",
        "--mdp_execution_delay_frozen_title=App isn't responding",
        "--mdp_execution_delay_frozen_message=The app is taking longer than usual to respond.",
    ]
  if profile_name == "partial_loading_skeleton":
    return [
        "--mdp_execution_delay_enable=True",
        "--mdp_execution_delay_trigger_steps=1",
        "--mdp_execution_delay_steps=2",
        "--mdp_execution_delay_mode=skeleton",
        "--mdp_execution_delay_block_actions=True",
        "--mdp_execution_delay_loading_text=Loading content...",
    ]
  if profile_name == "app_hang_restart_required":
    return [
        "--mdp_app_hang_enable=True",
        f"--mdp_app_hang_trigger_steps={args.app_hang_trigger_steps}",
        "--mdp_app_hang_title=App isn't responding",
        "--mdp_app_hang_message=This app stopped responding. Restart it to continue.",
        "--mdp_app_hang_restart_button=Restart app",
        "--mdp_app_hang_close_button=Close app",
        "--mdp_app_hang_settle_time_sec=1.0",
        "--mdp_app_hang_allow_home_recovery=True",
        "--mdp_app_hang_allow_open_app_recovery=True",
        "--mdp_app_hang_close_goes_home=True",
    ]
  if profile_name == "state_reset_home":
    return [
        "--mdp_state_reset_enable=True",
        "--mdp_state_reset_trigger_steps=2",
        "--mdp_state_reset_return_home=True",
        "--mdp_state_reset_settle_time_sec=1.0",
    ]
  if profile_name == "bottom_sheet_consent":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=popup",
        "--mdp_helper_interruption_surface_style=bottom_sheet",
        "--mdp_helper_interruption_app_name=News Daily",
        "--mdp_helper_interruption_title=Privacy choices",
        "--mdp_helper_interruption_message=Choose whether this app can use analytics and personalized content while you browse.",
        "--mdp_helper_interruption_primary_button=Accept",
        "--mdp_helper_interruption_secondary_button=Manage options",
        "--mdp_helper_interruption_primary_action=dismiss",
        "--mdp_helper_interruption_secondary_action=open_destination",
        "--mdp_helper_interruption_secondary_destination=privacy_options",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "popup_permission":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=popup",
        "--mdp_helper_interruption_surface_style=dialog",
        "--mdp_helper_interruption_app_name=Android System",
        "--mdp_helper_interruption_title=Allow notifications?",
        "--mdp_helper_interruption_message=Android System wants to send alerts while you use this app.",
        "--mdp_helper_interruption_primary_button=Allow",
        "--mdp_helper_interruption_secondary_button=Not now",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=notification_settings",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "popup_security":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=popup",
        "--mdp_helper_interruption_surface_style=dialog",
        "--mdp_helper_interruption_app_name=Security Center",
        "--mdp_helper_interruption_title=Verify this action",
        "--mdp_helper_interruption_message=This app is trying to change a protected system setting.",
        "--mdp_helper_interruption_primary_button=Continue",
        "--mdp_helper_interruption_secondary_button=Cancel",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=security_center",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "interstitial_ad":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=ad",
        "--mdp_helper_interruption_surface_style=interstitial",
        "--mdp_helper_interruption_app_name=Market Hub",
        "--mdp_helper_interruption_title=48-hour flash sale",
        "--mdp_helper_interruption_message=Save 60% on travel gear if you check out before midnight.",
        "--mdp_helper_interruption_primary_button=Shop now",
        "--mdp_helper_interruption_secondary_button=Maybe later",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=shopping_amazon",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "ad_trial_offer":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=ad",
        "--mdp_helper_interruption_surface_style=interstitial",
        "--mdp_helper_interruption_app_name=ShopEasy",
        "--mdp_helper_interruption_title=Try Premium for 30 days",
        "--mdp_helper_interruption_message=Unlock ad-free browsing, offline access, and exclusive themes.",
        "--mdp_helper_interruption_primary_button=Install",
        "--mdp_helper_interruption_secondary_button=Close",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=app_store_update",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "rate_dialog":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=popup",
        "--mdp_helper_interruption_surface_style=bottom_sheet",
        "--mdp_helper_interruption_app_name=Notes Pro",
        "--mdp_helper_interruption_title=Enjoying Notes Pro?",
        "--mdp_helper_interruption_message=Would you like to rate the app and tell us what is working well?",
        "--mdp_helper_interruption_primary_button=Rate now",
        "--mdp_helper_interruption_secondary_button=No thanks",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=rating_flow",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "update_system":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=update",
        "--mdp_helper_interruption_surface_style=dialog",
        "--mdp_helper_interruption_app_name=System updater",
        "--mdp_helper_interruption_title=Update available",
        "--mdp_helper_interruption_message=A newer version is ready with security fixes and improved stability.",
        "--mdp_helper_interruption_primary_button=Update now",
        "--mdp_helper_interruption_secondary_button=Later",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=system_update_settings",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=True",
    ]
  if profile_name == "update_app_sheet":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=update",
        "--mdp_helper_interruption_surface_style=bottom_sheet",
        "--mdp_helper_interruption_app_name=Maps Go",
        "--mdp_helper_interruption_title=New features are ready",
        "--mdp_helper_interruption_message=Get route previews, bug fixes, and improved battery performance.",
        "--mdp_helper_interruption_primary_button=Update",
        "--mdp_helper_interruption_secondary_button=Skip",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=app_store_update",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=False",
    ]
  if profile_name == "notification_message":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=notification",
        "--mdp_helper_interruption_surface_style=banner",
        "--mdp_helper_interruption_app_name=Messages",
        "--mdp_helper_interruption_title=New message",
        "--mdp_helper_interruption_message=Jordan: The meeting moved to 3:30 PM.",
        "--mdp_helper_interruption_primary_button=Open",
        "--mdp_helper_interruption_secondary_button=Dismiss",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=message_thread",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=False",
        "--mdp_helper_interruption_auto_dismiss_ms=0",
    ]
  if profile_name == "notification_delivery":
    return [
        "--mdp_helper_interruption_enable=True",
        "--mdp_helper_interruption_trigger_steps=1",
        "--mdp_helper_interruption_kind=notification",
        "--mdp_helper_interruption_surface_style=banner",
        "--mdp_helper_interruption_app_name=Parcel Tracker",
        "--mdp_helper_interruption_title=Driver is nearby",
        "--mdp_helper_interruption_message=Your package will arrive in the next 5 minutes.",
        "--mdp_helper_interruption_primary_button=Track",
        "--mdp_helper_interruption_secondary_button=Dismiss",
        "--mdp_helper_interruption_primary_action=open_destination",
        "--mdp_helper_interruption_primary_destination=delivery_tracking",
        "--mdp_helper_interruption_secondary_action=dismiss",
        "--mdp_helper_interruption_blocking=False",
        "--mdp_helper_interruption_auto_dismiss_ms=4000",
    ]
  if profile_name == "locale_date_format_us12":
    return [
        "--mdp_locale_date_format_enable=True",
        "--mdp_locale_date_format_activation_mode=on_reset",
        "--mdp_locale_date_format_trigger_steps=1",
        "--mdp_locale_date_format_time_format=12",
        "--mdp_locale_date_format_date_format=MM-dd-yyyy",
        "--mdp_locale_date_format_settle_time_sec=1.0",
        "--mdp_locale_date_format_restore_on_close=True",
    ]
  if profile_name == "locale_date_format_eu24":
    return [
        "--mdp_locale_date_format_enable=True",
        "--mdp_locale_date_format_activation_mode=on_reset",
        "--mdp_locale_date_format_trigger_steps=1",
        "--mdp_locale_date_format_time_format=24",
        "--mdp_locale_date_format_date_format=dd-MM-yyyy",
        "--mdp_locale_date_format_settle_time_sec=1.0",
        "--mdp_locale_date_format_restore_on_close=True",
    ]
  if profile_name == "action_delay_realistic":
    return [
        "--mdp_action_delay_enable=True",
        f"--mdp_action_delay_probability={args.action_delay_probability}",
        f"--mdp_action_delay_seconds={args.action_delay_seconds}",
        f"--mdp_action_delay_seed={args.action_delay_seed}",
    ]
  if profile_name == "action_drop_random":
    return [
        "--mdp_action_drop_enable=True",
        f"--mdp_action_drop_probability={args.action_drop_probability}",
        f"--mdp_action_drop_seed={args.action_drop_seed}",
    ]
  raise ValueError(f"Unsupported perturbation profile: {profile_name}")


def _sanitize_task_name(task: str) -> str:
  return "".join(char if char.isalnum() else "_" for char in task).strip("_") or "task"


def _make_names(task: str, repeat_index: int, trajs_dir: Path, logs_dir: Path) -> tuple[str, str]:
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  task_slug = _sanitize_task_name(task)
  traj = trajs_dir / f"traj_{task_slug}_r{repeat_index}_{timestamp}"
  log = logs_dir / f"log_{task_slug}_r{repeat_index}_{timestamp}.log"
  return str(traj), str(log)


def _write_text(handle, message: str) -> None:
  data = message.encode("utf-8", errors="ignore")
  handle.write(data)
  handle.flush()


def _stream_subprocess(
    cmd: list[str],
    combined_log_handle,
    per_run_log_path: str,
) -> int:
  with open(per_run_log_path, "wb") as per_run_log:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert process.stdout is not None
    for chunk in iter(lambda: process.stdout.read(1024), b""):
      per_run_log.write(chunk)
      per_run_log.flush()
      combined_log_handle.write(chunk)
      combined_log_handle.flush()
      try:
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
      except Exception:
        pass
    return process.wait()


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--suite-family", default="android_world")
  parser.add_argument("--tasks", default="")
  parser.add_argument("--tasks-file", default="")
  parser.add_argument("--repeats-per-task", type=int, default=3)
  parser.add_argument("--agent", default="gui_owl")
  parser.add_argument("--model", default="gui_owl")
  parser.add_argument("--api-key", dest="api_key", default="sk-local")
  parser.add_argument("--base-url", dest="base_url", default="http://127.0.0.1:4243/v1")
  parser.add_argument("--guiowl-coordinate-format", default="abs_resized")
  parser.add_argument("--guiowl-temperature", type=float, default=0.0)
  parser.add_argument("--grpc-port", type=int, default=8554)
  parser.add_argument("--console-port", type=int, default=5554)
  parser.add_argument("--adb-path", default="")
  parser.add_argument("--perform-emulator-setup", default="False")
  parser.add_argument("--sampling-seed", type=int, default=20260414)
  parser.add_argument(
      "--profiles",
      default="",
      help=(
          "Optional comma-separated subset of perturbation profiles to sample "
          "from. If clean is enabled, it remains eligible unless disabled."
      ),
  )
  parser.add_argument("--font-size-large-scale", type=float, default=1.35)
  parser.add_argument("--font-size-small-scale", type=float, default=0.82)
  parser.add_argument("--display-compact-density-scale", type=float, default=0.85)
  parser.add_argument("--display-compact-size-scale", type=float, default=0.94)
  parser.add_argument("--display-zoomed-out-density-scale", type=float, default=0.76)
  parser.add_argument("--display-zoomed-out-size-scale", type=float, default=0.88)
  parser.add_argument("--orientation-profile-trigger-steps", default="1,3")
  parser.add_argument("--orientation-profile-sequence", default="landscape")
  parser.add_argument("--app-hang-trigger-steps", default="2")
  parser.add_argument("--action-delay-probability", type=float, default=0.15)
  parser.add_argument("--action-delay-seconds", type=float, default=1.5)
  parser.add_argument("--action-delay-seed", type=int, default=0)
  parser.add_argument("--action-drop-probability", type=float, default=0.08)
  parser.add_argument("--action-drop-seed", type=int, default=0)
  parser.add_argument("--downstream-pre-action-enable", default="False")
  parser.add_argument("--downstream-pre-action-log-enable", default="True")
  parser.add_argument("--downstream-pre-action-use-recovery-prompt", default="True")
  parser.add_argument("--downstream-pre-action-wait-seconds", type=float, default=3.0)
  parser.add_argument("--downstream-recovery-max-steps", type=int, default=3)
  parser.add_argument("--downstream-hard-stuck-window", type=int, default=5)
  parser.add_argument("--episode-step-budget-multiplier", type=float, default=15.0)
  parser.add_argument("--disable-clean", action="store_true")
  parser.add_argument("--session-dir", default="")
  args = parser.parse_args()

  tasks = _resolve_tasks(args)
  if not tasks:
    print("No tasks resolved for the random perturbation runner.")
    return

  profiles = _select_profiles(
      _build_profiles(include_clean=not args.disable_clean),
      args.profiles,
  )
  session_paths = _prepare_session_directories(args.session_dir)
  session_dir = session_paths["session_dir"]
  logs_dir = session_paths["logs_dir"]
  trajs_dir = session_paths["trajs_dir"]
  android_world_runs_dir = session_paths["android_world_runs_dir"]
  session_timestamp = session_dir.name
  combined_log_path = str(session_dir / "combined.log")
  manifest_path = str(session_dir / "manifest.jsonl")
  summary_path = str(session_dir / "summary.json")

  results: list[dict[str, object]] = []
  base_rng = random.Random(args.sampling_seed)

  with open(combined_log_path, "wb") as combined_log, open(
      manifest_path,
      "w",
      encoding="utf-8",
  ) as manifest_file:
    header = (
        f"Random perturbation batch start: {session_timestamp}\n"
        f"Suite family: {args.suite_family}\n"
        f"Tasks: {len(tasks)}\n"
        f"Repeats per task: {args.repeats_per_task}\n"
        f"Profiles: {[profile.name for profile in profiles]}\n\n"
    )
    _write_text(combined_log, header)
    try:
      sys.stdout.write(header)
      sys.stdout.flush()
    except Exception:
      pass

    for task_index, task in enumerate(tasks, start=1):
      task_rng = random.Random(f"{args.sampling_seed}:{task}:{task_index}:{base_rng.random()}")
      sampled_profiles = _sample_profiles_for_task(
          task_rng, profiles, args.repeats_per_task
      )
      for repeat_index, profile in enumerate(sampled_profiles, start=1):
        traj_path, per_run_log_path = _make_names(
            task, repeat_index, trajs_dir, logs_dir
        )
        cmd = [
            PY_CMD,
            RUN_SCRIPT,
            f"--suite_family={args.suite_family}",
            f"--tasks={task}",
            "--n_task_combinations=1",
            f"--agent_name={args.agent}",
            f"--model={args.model}",
            f"--api_key={args.api_key}",
            f"--base_url={args.base_url}",
            f"--guiowl_coordinate_format={args.guiowl_coordinate_format}",
            f"--guiowl_temperature={args.guiowl_temperature}",
            f"--downstream_pre_action_enable={args.downstream_pre_action_enable}",
            f"--downstream_pre_action_log_enable={args.downstream_pre_action_log_enable}",
            f"--downstream_pre_action_use_recovery_prompt={args.downstream_pre_action_use_recovery_prompt}",
            f"--downstream_pre_action_wait_seconds={args.downstream_pre_action_wait_seconds}",
            f"--downstream_recovery_max_steps={args.downstream_recovery_max_steps}",
            f"--downstream_hard_stuck_window={args.downstream_hard_stuck_window}",
            f"--episode_step_budget_multiplier={args.episode_step_budget_multiplier}",
            f"--output_path={android_world_runs_dir}",
            f"--traj_output_path={traj_path}",
            f"--grpc_port={args.grpc_port}",
            f"--console_port={args.console_port}",
        ]
        if args.adb_path:
          cmd.append(f"--adb_path={args.adb_path}")
        if args.perform_emulator_setup:
          cmd.append(f"--perform_emulator_setup={args.perform_emulator_setup}")

        perturbation_flags = _perturbation_flags(profile.name, args)
        cmd.extend(perturbation_flags)

        manifest_record = {
            "task": task,
            "repeat_index": repeat_index,
            "profile_name": profile.name,
            "profile_description": profile.description,
            "traj_output_path": traj_path,
            "per_run_log_path": per_run_log_path,
            "command": cmd,
        }
        manifest_file.write(json.dumps(manifest_record, ensure_ascii=False) + "\n")
        manifest_file.flush()

        run_header = (
            f"\n[RUN] task={task} repeat={repeat_index}/{args.repeats_per_task} "
            f"profile={profile.name} traj={traj_path} log={per_run_log_path}\n"
        )
        _write_text(combined_log, run_header)
        try:
          sys.stdout.write(run_header)
          sys.stdout.flush()
        except Exception:
          pass

        return_code = _stream_subprocess(cmd, combined_log, per_run_log_path)
        success, success_source = _extract_success_from_log(
            task=task,
            log_path=per_run_log_path,
            return_code=return_code,
        )
        results.append(
            {
                "task": task,
                "repeat_index": repeat_index,
                "profile_name": profile.name,
                "return_code": return_code,
                "success": success,
                "success_source": success_source,
                "traj_output_path": traj_path,
                "per_run_log_path": per_run_log_path,
            }
        )

  repeat_summary = _aggregate_success_by_key(results, "repeat_index")
  profile_summary = _aggregate_success_by_key(results, "profile_name")

  with open(summary_path, "w", encoding="utf-8") as summary_file:
    json.dump(
        {
            "suite_family": args.suite_family,
            "repeats_per_task": args.repeats_per_task,
            "profiles": [profile.name for profile in profiles],
            "results": results,
            "repeat_summary": repeat_summary,
            "profile_summary": profile_summary,
            "combined_log_path": combined_log_path,
            "manifest_path": manifest_path,
        },
        summary_file,
        indent=2,
        ensure_ascii=False,
    )

  print("Success rate by repeat:")
  for repeat_index, stats in repeat_summary.items():
    print(
        f"  repeat {repeat_index}: "
        f"{stats['num_successes']}/{stats['num_runs']} "
        f"({stats['success_rate']:.3f})"
    )
  print(f"Session dir: {session_dir}")
  print(f"Combined log: {combined_log_path}")
  print(f"Manifest: {manifest_path}")
  print(f"Summary: {summary_path}")


if __name__ == "__main__":
  main()
