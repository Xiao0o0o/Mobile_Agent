"""Real-emulator preview script for date/time format perturbation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(_PROJECT_ROOT))

from android_world.agents import new_json_action as json_action
from android_world.env import adb_utils
from android_world.env import env_launcher
from mdp_perturbation.locale_date_format import LocaleDateFormatPerturbationConfig
from mdp_perturbation.locale_date_format import LocaleDateFormatPerturbationEnv
from PIL import Image


def _find_adb_directory() -> str:
  potential_paths = [
      os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
      os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
      "/root/android/android_sdk/platform-tools/adb",
  ]
  for path in potential_paths:
    if os.path.isfile(path):
      return path
  raise EnvironmentError("adb not found in the common Android SDK paths.")


def _save_image(image, path: str) -> None:
  Image.fromarray(image).save(path)


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--console-port", type=int, default=5554)
  parser.add_argument("--grpc-port", type=int, default=8554)
  parser.add_argument("--adb-path", default=_find_adb_directory())
  parser.add_argument(
      "--output-dir",
      default=os.path.join(os.path.dirname(__file__), "demo_output"),
  )
  parser.add_argument("--prepare-app", default="clock")
  parser.add_argument("--time-format", choices=("12", "24"), default="24")
  parser.add_argument("--date-format", default="dd-MM-yyyy")
  parser.add_argument("--settle-time-sec", type=float, default=1.0)
  parser.add_argument(
      "--trigger-action",
      choices=("wait", "home", "open_app"),
      default="wait",
  )
  parser.add_argument("--trigger-open-app", default="clock")
  args = parser.parse_args()

  os.makedirs(args.output_dir, exist_ok=True)
  env = env_launcher.load_and_setup_env(
      console_port=args.console_port,
      emulator_setup=False,
      freeze_datetime=True,
      adb_path=args.adb_path,
      grpc_port=args.grpc_port,
  )
  wrapped_env = LocaleDateFormatPerturbationEnv(
      env,
      LocaleDateFormatPerturbationConfig(
          enabled=True,
          trigger_steps=(1,),
          time_format=args.time_format,
          date_format=args.date_format,
          settle_time_sec=args.settle_time_sec,
          restore_on_close=True,
      ),
  )

  try:
    adb_utils.launch_app(args.prepare_app, env.controller)
    before_state = wrapped_env.get_state(wait_to_stabilize=True)
    before_path = os.path.join(args.output_dir, "locale_date_format_before.png")
    _save_image(before_state.pixels, before_path)
    print(f"Saved before screenshot to: {before_path}")
    print(before_state.auxiliaries.get("mdp_locale_date_format", {}))

    if args.trigger_action == "home":
      action = json_action.JSONAction(action_type=json_action.NAVIGATE_HOME)
    elif args.trigger_action == "open_app":
      action = json_action.JSONAction(
          action_type=json_action.OPEN_APP,
          app_name=args.trigger_open_app,
      )
    else:
      action = json_action.JSONAction(action_type=json_action.WAIT)

    wrapped_env.execute_action(action)
    after_state = wrapped_env.get_state(wait_to_stabilize=True)
    after_path = os.path.join(args.output_dir, "locale_date_format_after.png")
    _save_image(after_state.pixels, after_path)
    print(f"Saved after screenshot to: {after_path}")
    print(after_state.auxiliaries.get("mdp_locale_date_format", {}))
  finally:
    wrapped_env.close()


if __name__ == "__main__":
  main()
