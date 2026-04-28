package com.google.androidenv.perturbationhelper

enum class InterruptionType(
  val wireValue: String,
  val displayName: String,
  val badge: String,
) {
  POPUP("popup", "Popup", "System"),
  AD("ad", "Ad", "Sponsored"),
  UPDATE("update", "Update", "Update"),
  NOTIFICATION("notification", "Notification", "Alert");

  companion object {
    fun fromWireValue(value: String?): InterruptionType {
      return entries.firstOrNull { it.wireValue.equals(value, ignoreCase = true) } ?: POPUP
    }
  }
}
