package com.google.androidenv.perturbationhelper

import android.content.Intent
import java.util.UUID

data class InterruptionSpec(
  val type: InterruptionType,
  val surfaceStyle: InterruptionSurfaceStyle,
  val appName: String,
  val title: String,
  val message: String,
  val primaryButton: String,
  val secondaryButton: String,
  val blocking: Boolean,
  val autoDismissMs: Long,
  val primaryAction: String = "",
  val secondaryAction: String = "",
  val primaryDestination: String = "",
  val secondaryDestination: String = "",
  val instanceId: String = UUID.randomUUID().toString(),
) {
  fun toIntent(): Intent {
    return Intent(InterruptionContract.ACTION_SHOW_INTERRUPTION).apply {
      putExtra(InterruptionContract.EXTRA_KIND, this@InterruptionSpec.type.wireValue)
      putExtra(
        InterruptionContract.EXTRA_SURFACE_STYLE,
        this@InterruptionSpec.surfaceStyle.wireValue,
      )
      putExtra(InterruptionContract.EXTRA_APP_NAME, appName)
      putExtra(InterruptionContract.EXTRA_TITLE, title)
      putExtra(InterruptionContract.EXTRA_MESSAGE, message)
      putExtra(InterruptionContract.EXTRA_PRIMARY_BUTTON, primaryButton)
      putExtra(InterruptionContract.EXTRA_SECONDARY_BUTTON, secondaryButton)
      putExtra(InterruptionContract.EXTRA_BLOCKING, blocking)
      putExtra(InterruptionContract.EXTRA_AUTO_DISMISS_MS, autoDismissMs)
      putExtra(InterruptionContract.EXTRA_PRIMARY_ACTION, primaryAction)
      putExtra(InterruptionContract.EXTRA_SECONDARY_ACTION, secondaryAction)
      putExtra(InterruptionContract.EXTRA_PRIMARY_DESTINATION, primaryDestination)
      putExtra(InterruptionContract.EXTRA_SECONDARY_DESTINATION, secondaryDestination)
      putExtra(InterruptionContract.EXTRA_INSTANCE_ID, instanceId)
    }
  }

  companion object {
    fun fromIntent(intent: Intent): InterruptionSpec {
      val type = InterruptionType.fromWireValue(
        intent.getStringExtra(InterruptionContract.EXTRA_KIND)
      )
      val defaults = PresetRepository.defaultSpecFor(type)
      return InterruptionNavigation.resolve(
        defaults.copy(
          surfaceStyle = intent.getStringExtra(InterruptionContract.EXTRA_SURFACE_STYLE)?.let {
            InterruptionSurfaceStyle.fromWireValue(it)
          } ?: defaults.surfaceStyle,
          appName = intent.getStringExtra(InterruptionContract.EXTRA_APP_NAME) ?: defaults.appName,
          title = intent.getStringExtra(InterruptionContract.EXTRA_TITLE) ?: defaults.title,
          message = intent.getStringExtra(InterruptionContract.EXTRA_MESSAGE) ?: defaults.message,
          primaryButton = intent.getStringExtra(InterruptionContract.EXTRA_PRIMARY_BUTTON)
            ?: defaults.primaryButton,
          secondaryButton = intent.getStringExtra(InterruptionContract.EXTRA_SECONDARY_BUTTON)
            ?: defaults.secondaryButton,
          blocking =
            intent.getBooleanExtra(InterruptionContract.EXTRA_BLOCKING, defaults.blocking),
          autoDismissMs = intent.getLongExtra(
            InterruptionContract.EXTRA_AUTO_DISMISS_MS,
            defaults.autoDismissMs,
          ),
          primaryAction =
            intent.getStringExtra(InterruptionContract.EXTRA_PRIMARY_ACTION).orEmpty(),
          secondaryAction =
            intent.getStringExtra(InterruptionContract.EXTRA_SECONDARY_ACTION).orEmpty(),
          primaryDestination =
            intent.getStringExtra(InterruptionContract.EXTRA_PRIMARY_DESTINATION).orEmpty(),
          secondaryDestination =
            intent.getStringExtra(InterruptionContract.EXTRA_SECONDARY_DESTINATION).orEmpty(),
          instanceId = intent.getStringExtra(InterruptionContract.EXTRA_INSTANCE_ID)
            ?: defaults.instanceId,
        )
      )
    }
  }
}
