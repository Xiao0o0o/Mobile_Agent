"""Real-emulator preview script for execution-delay perturbation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(_PROJECT_ROOT))

from android_world.env import env_launcher
from android_world.agents import new_json_action as json_action
from mdp_perturbation.execution_delay import ExecutionDelayPerturbationConfig
from mdp_perturbation.execution_delay import ExecutionDelayPerturbationEnv
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


def _build_demo_action(action_name: str, app_name: str):
  if action_name == "open_settings":
    return json_action.JSONAction(action_type=json_action.OPEN_APP, app_name=app_name)
  if action_name == "home":
    return json_action.JSONAction(action_type=json_action.NAVIGATE_HOME)
  if action_name == "wait":
    return json_action.JSONAction(action_type=json_action.WAIT)
  raise ValueError(f"Unsupported demo action: {action_name}")


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--console-port", type=int, default=5554)
  parser.add_argument("--grpc-port", type=int, default=8554)
  parser.add_argument("--adb-path", default=_find_adb_directory())
  parser.add_argument(
      "--output-dir",
      default=os.path.join(os.path.dirname(__file__), "demo_output"),
  )
  parser.add_argument(
      "--mode",
      choices=("loading", "frozen", "skeleton"),
      default="loading",
  )
  parser.add_argument("--delay-steps", type=int, default=2)
  parser.add_argument(
      "--demo-action",
      choices=("open_settings", "home", "wait"),
      default="open_settings",
  )
  parser.add_argument("--app-name", default="settings")
  args = parser.parse_args()

  os.makedirs(args.output_dir, exist_ok=True)
  env = env_launcher.load_and_setup_env(
      console_port=args.console_port,
      emulator_setup=False,
      freeze_datetime=True,
      adb_path=args.adb_path,
      grpc_port=args.grpc_port,
  )
  wrapped_env = ExecutionDelayPerturbationEnv(
      env,
      ExecutionDelayPerturbationConfig(
          enabled=True,
          trigger_steps=(1,),
          delay_steps=args.delay_steps,
          mode=args.mode,
      ),
  )

  try:
    before_state = wrapped_env.get_state(wait_to_stabilize=False)
    before_path = os.path.join(args.output_dir, "execution_delay_before.png")
    _save_image(before_state.pixels, before_path)
    print(f"Saved before screenshot to: {before_path}")

    wrapped_env.execute_action(_build_demo_action(args.demo_action, args.app_name))

    during_state = wrapped_env.get_state(wait_to_stabilize=False)
    during_path = os.path.join(args.output_dir, "execution_delay_during.png")
    _save_image(during_state.pixels, during_path)
    print(f"Saved during-delay screenshot to: {during_path}")
    print(during_state.auxiliaries.get("mdp_execution_delay", {}))

    final_state = during_state
    for _ in range(args.delay_steps):
      final_state = wrapped_env.get_state(wait_to_stabilize=False)

    after_path = os.path.join(args.output_dir, "execution_delay_after.png")
    _save_image(final_state.pixels, after_path)
    print(f"Saved after-delay screenshot to: {after_path}")
    print(final_state.auxiliaries.get("mdp_execution_delay", {}))
  finally:
    wrapped_env.close()


if __name__ == "__main__":
  main()
