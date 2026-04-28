package com.google.androidenv.perturbationhelper

private const val ACTION_DISMISS = "dismiss"
private const val ACTION_OPEN_DESTINATION = "open_destination"

object InterruptionNavigation {

  fun resolve(spec: InterruptionSpec): InterruptionSpec {
    val primaryDestination = spec.primaryDestination.ifBlank {
      inferDestination(spec, isPrimary = true)
    }
    val secondaryDestination = spec.secondaryDestination.ifBlank {
      inferDestination(spec, isPrimary = false)
    }
    val primaryAction = resolveAction(spec.primaryAction, primaryDestination)
    val secondaryAction = resolveAction(spec.secondaryAction, secondaryDestination)
    return spec.copy(
      primaryAction = primaryAction,
      secondaryAction = secondaryAction,
      primaryDestination =
        if (primaryAction == ACTION_OPEN_DESTINATION) primaryDestination else "",
      secondaryDestination =
        if (secondaryAction == ACTION_OPEN_DESTINATION) secondaryDestination else "",
    )
  }

  private fun resolveAction(rawAction: String, destination: String): String {
    val normalized = rawAction.normalized()
    return when {
      normalized.isBlank() ->
        if (destination.isNotBlank()) ACTION_OPEN_DESTINATION else ACTION_DISMISS
      normalized == ACTION_OPEN_DESTINATION && destination.isNotBlank() ->
        ACTION_OPEN_DESTINATION
      else -> ACTION_DISMISS
    }
  }

  private fun inferDestination(spec: InterruptionSpec, isPrimary: Boolean): String {
    val buttonText = (if (isPrimary) spec.primaryButton else spec.secondaryButton).normalized()
    val content = listOf(
      spec.appName,
      spec.title,
      spec.message,
      spec.primaryButton,
      spec.secondaryButton,
    ).joinToString(" ").normalized()

    if (
      !isPrimary &&
      content.containsAny("privacy choices", "analytics", "personalized content", "cookies") &&
      buttonText.containsAny("manage", "options", "choices", "settings")
    ) {
      return "privacy_options"
    }

    if (
      content.containsAny(
        "rate this app",
        "enjoying",
        "how was your experience",
        "tell us what is working well",
      ) || buttonText.containsAny("rate", "review", "stars", "submit")
    ) {
      return if (isPrimary) "rating_flow" else ""
    }

    if (
      spec.type == InterruptionType.UPDATE ||
      content.containsAny(
        "update available",
        "new version",
        "security fixes",
        "system update",
        "what's new",
        "bug fixes",
      )
    ) {
      if (
        !isPrimary &&
        !buttonText.containsAny("view", "details", "open", "learn more", "all updates")
      ) {
        return ""
      }
      return if (
        content.containsAny(
          "system updater",
          "android system",
          "system update",
          "security patch",
          "restart required",
        )
      ) {
        "system_update_settings"
      } else {
        "app_store_update"
      }
    }

    if (spec.type == InterruptionType.NOTIFICATION) {
      return when {
        content.containsAny("driver", "delivery", "package", "parcel", "track") ||
          buttonText.containsAny("track", "map") ->
          if (isPrimary) "delivery_tracking" else ""
        else -> if (isPrimary) "message_thread" else ""
      }
    }

    if (
      content.containsAny(
        "verify this action",
        "protected system setting",
        "security center",
        "risk summary",
        "protected action review",
      )
    ) {
      return if (isPrimary || buttonText.containsAny("continue", "approve", "review")) {
        "security_center"
      } else {
        ""
      }
    }

    if (
      content.containsAny(
        "allow notifications",
        "notification permissions",
        "send alerts",
        "alerts while you use this app",
      ) && buttonText.containsAny("allow", "continue", "open", "settings")
    ) {
      return "notification_settings"
    }

    if (
      spec.type == InterruptionType.AD ||
      content.containsAny("flash sale", "travel gear", "shop", "deals", "cart", "prime badge")
    ) {
      return when {
        buttonText.containsAny("shop", "cart", "deal", "buy", "open") -> "shopping_amazon"
        isPrimary && buttonText.containsAny("install", "download", "get") -> "app_store_update"
        else -> ""
      }
    }

    return ""
  }
}

private fun String.normalized(): String = trim().lowercase()

private fun String.containsAny(vararg tokens: String): Boolean =
  tokens.any { contains(it) }
