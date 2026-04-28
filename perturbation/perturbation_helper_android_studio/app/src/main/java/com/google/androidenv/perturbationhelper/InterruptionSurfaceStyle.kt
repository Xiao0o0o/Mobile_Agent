package com.google.androidenv.perturbationhelper

enum class InterruptionSurfaceStyle(
  val wireValue: String,
  val displayName: String,
) {
  DIALOG("dialog", "Dialog"),
  BOTTOM_SHEET("bottom_sheet", "Bottom sheet"),
  INTERSTITIAL("interstitial", "Interstitial"),
  BANNER("banner", "Banner");

  companion object {
    fun fromWireValue(value: String?): InterruptionSurfaceStyle {
      return entries.firstOrNull { it.wireValue.equals(value, ignoreCase = true) } ?: DIALOG
    }
  }
}
