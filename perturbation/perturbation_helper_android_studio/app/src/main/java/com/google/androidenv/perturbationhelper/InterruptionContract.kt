package com.google.androidenv.perturbationhelper

object InterruptionContract {
  const val ACTION_SHOW_INTERRUPTION =
    "com.google.androidenv.perturbationhelper.SHOW_INTERRUPTION"
  const val ACTION_INTERRUPTION_RESULT =
    "com.google.androidenv.perturbationhelper.INTERRUPTION_RESULT"

  const val EXTRA_KIND = "kind"
  const val EXTRA_SURFACE_STYLE = "surface_style"
  const val EXTRA_TITLE = "title"
  const val EXTRA_MESSAGE = "message"
  const val EXTRA_APP_NAME = "app_name"
  const val EXTRA_PRIMARY_BUTTON = "primary_button"
  const val EXTRA_SECONDARY_BUTTON = "secondary_button"
  const val EXTRA_BLOCKING = "blocking"
  const val EXTRA_AUTO_DISMISS_MS = "auto_dismiss_ms"
  const val EXTRA_PRIMARY_ACTION = "primary_action"
  const val EXTRA_SECONDARY_ACTION = "secondary_action"
  const val EXTRA_PRIMARY_DESTINATION = "primary_destination"
  const val EXTRA_SECONDARY_DESTINATION = "secondary_destination"
  const val EXTRA_INSTANCE_ID = "instance_id"
  const val EXTRA_RESULT = "result"
  const val EXTRA_TIMESTAMP = "timestamp"

  const val RESULT_PRIMARY = "primary"
  const val RESULT_SECONDARY = "secondary"
  const val RESULT_BACKGROUND = "background"
  const val RESULT_TIMEOUT = "timeout"
  const val RESULT_BACK = "back"
  const val RESULT_SWIPE = "swipe"
}
