# Perturbation Helper Android Studio App

This is a standalone Android Studio project for real, interactive perturbations.

## Included interruption types

- Popup
- Ad
- Update
- Notification

## Included surface styles

- Dialog
- Bottom sheet
- Interstitial
- Banner

## What it provides

- A launcher dashboard with preset galleries
- A configurable interruption composer
- A benchmark-facing `InterruptionActivity`
- Result broadcasts for button press, swipe dismiss, timeout, background dismiss, and back dismiss

## Open in Android Studio

Open this directory directly:

`/home/local/ASURITE/xiaoouli/MobileAgent-main/Mobile-Agent-v3/android_world_v3/perturbation_helper_android_studio`

## Build APK

Use Android Studio:

1. Open the project
2. Let Gradle sync
3. Run `app` on your emulator, or build `app-debug.apk`

Note:

- The Android Gradle Plugin in this project requires Java 17.
- On this machine, command-line Gradle validation reached the Android plugin, but the local JDK was Java 11, so a full assemble could not complete until Java 17 is selected in Android Studio or via `JAVA_HOME`.

## Benchmark intent contract

Action:

`com.google.androidenv.perturbationhelper.SHOW_INTERRUPTION`

Supported extras:

- `kind`
- `surface_style`
- `title`
- `message`
- `app_name`
- `primary_button`
- `secondary_button`
- `blocking`
- `auto_dismiss_ms`
- `primary_action`
- `secondary_action`
- `primary_destination`
- `secondary_destination`
- `instance_id`

Result broadcast:

`com.google.androidenv.perturbationhelper.INTERRUPTION_RESULT`
