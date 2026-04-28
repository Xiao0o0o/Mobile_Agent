# Perturbation Helper App

This helper app is now intended to live as a standalone Android Studio project,
separate from the existing Bazel app tree. It is the recommended path for real,
interactive interruptions that are more natural than screenshot-only overlays.

## Scope

Use the helper app for:

- `popup`
- `ad`
- `update`
- `notification`

Keep these perturbations in Python wrappers:

- `coordinate_noise`
- `execution_delay`
- `resolution / screenshot quality`
- `theme`
- `state_reset`

## Android Studio Project

Open this directory in Android Studio:

`/home/local/ASURITE/xiaoouli/MobileAgent-main/Mobile-Agent-v3/android_world_v3/perturbation_helper_android_studio`

The launcher app includes:

- preset galleries for popup / ad / update / notification
- a composer screen for editing title, message, buttons, blocking mode, and timeout
- a result log that shows how each interruption was dismissed

## Android Entry Point

- Package: `com.google.androidenv.perturbationhelper`
- Activity: `com.google.androidenv.perturbationhelper.app.InterruptionActivity`
- Intent action:
  `com.google.androidenv.perturbationhelper.SHOW_INTERRUPTION`

## Supported Extras

- `kind`: `popup | ad | update | notification`
- `title`
- `message`
- `app_name`
- `primary_button`
- `secondary_button`
- `blocking`
- `auto_dismiss_ms`
- `instance_id`

## Python Trigger

Use [helper_app.py](/home/local/ASURITE/xiaoouli/MobileAgent-main/Mobile-Agent-v3/android_world_v3/mdp_perturbation/helper_app.py)
to start the helper app from a wrapper.

## Build Sketch

From Android Studio:

1. Open the standalone project
2. Let Gradle sync
3. Run the `app` module on the emulator or build `app-debug.apk`
4. Install it on the AndroidWorld emulator

After the APK is installed, wrappers can trigger it with adb intents.

## Benchmark Flow

1. Install the helper app on the emulator
2. Trigger an interruption from Python using
   [helper_app.py](/home/local/ASURITE/xiaoouli/MobileAgent-main/Mobile-Agent-v3/android_world_v3/mdp_perturbation/helper_app.py)
3. Let the agent interact with the real interruption activity
4. Observe result broadcasts or simply continue after the activity finishes

## Next Good Extensions

- Add a notification overlay `Service` for true non-blocking banner behavior.
- Add a result receiver so Python can observe which button the agent pressed.
- Add templated variants for ad networks, update prompts, and permission-like dialogs.
