"""Real-emulator preview script for the standalone helper app."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(_PROJECT_ROOT))

from android_world.env import adb_utils
from android_world.env import env_launcher
from mdp_perturbation.helper_app import HelperInterruptionSpec
from mdp_perturbation.helper_app import show_helper_interruption
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
  parser.add_argument("--prepare-app", default="settings")
  parser.add_argument(
      "--kind",
      choices=("popup", "ad", "update", "notification"),
      default="popup",
  )
  parser.add_argument(
      "--surface-style",
      choices=("auto", "dialog", "bottom_sheet", "interstitial", "banner"),
      default="auto",
  )
  parser.add_argument("--title", default="Update available")
  parser.add_argument(
      "--message",
      default="A newer version is ready with security fixes and improved stability.",
  )
  parser.add_argument("--app-name", default="System updater")
  parser.add_argument("--primary-button", default="Update now")
  parser.add_argument("--secondary-button", default="Later")
  parser.add_argument("--blocking", action="store_true")
  parser.add_argument("--auto-dismiss-ms", type=int, default=0)
  parser.add_argument("--wait-sec", type=float, default=1.5)
  args = parser.parse_args()

  os.makedirs(args.output_dir, exist_ok=True)
  env = env_launcher.load_and_setup_env(
      console_port=args.console_port,
      emulator_setup=False,
      freeze_datetime=True,
      adb_path=args.adb_path,
      grpc_port=args.grpc_port,
  )

  try:
    adb_utils.launch_app(args.prepare_app, env.controller)
    before_state = env.get_state(wait_to_stabilize=True)
    before_path = os.path.join(args.output_dir, "helper_app_before.png")
    _save_image(before_state.pixels, before_path)
    print(f"Saved before screenshot to: {before_path}")

    show_helper_interruption(
        HelperInterruptionSpec(
            kind=args.kind,
            surface_style="" if args.surface_style == "auto" else args.surface_style,
            title=args.title,
            message=args.message,
            app_name=args.app_name,
            primary_button=args.primary_button,
            secondary_button=args.secondary_button,
            blocking=args.blocking,
            auto_dismiss_ms=args.auto_dismiss_ms,
        ),
        env.controller,
    )
    time.sleep(max(args.wait_sec, 0.0))

    after_state = env.get_state(wait_to_stabilize=True)
    after_path = os.path.join(args.output_dir, "helper_app_after.png")
    _save_image(after_state.pixels, after_path)
    print(f"Saved after screenshot to: {after_path}")
    print("If the after screenshot still shows the underlying app only,")
    print("the standalone helper APK is probably not installed on the emulator yet.")
  finally:
    env.close()


if __name__ == "__main__":
  main()
