package com.google.androidenv.perturbationhelper

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.activity.addCallback
import androidx.appcompat.app.AppCompatActivity
import com.google.androidenv.perturbationhelper.databinding.ActivityDestinationBinding

class DestinationActivity : AppCompatActivity() {

  private lateinit var binding: ActivityDestinationBinding
  private val backStack = mutableListOf<String>()

  private var notificationsEnabled = false
  private var notificationPopOnScreen = false
  private var notificationLockScreen = true
  private var categoryDirectMessages = true
  private var categoryMentions = true
  private var categoryReminders = false

  private var privacyAnalytics = true
  private var privacyPersonalized = false
  private var privacyMarketing = false
  private var privacyLocation = false
  private var vendorNewsDaily = true
  private var vendorAudienceLab = false
  private var vendorAdExchange = false
  private var vendorMeasurementStudio = false

  private var ratingStars = 0f
  private var reasonEaseOfUse = false
  private var reasonUseful = false
  private var reasonDesign = false
  private var reasonBugs = false
  private var reviewDraft = ""

  private var selectedDeal = ""
  private var filterPrimeOnly = true
  private var filterUnderFifty = false
  private var filterCarryOn = true
  private var filterFreeReturns = false
  private var selectedShipping = ""
  private var addProtectionPlan = false
  private var saveWishlist = false
  private var applyCoupon = false
  private var giftWrap = false
  private var selectedColor = ""
  private var selectedFulfillment = ""
  private var selectedPaymentMethod = ""

  private var replyDraft = ""
  private var includeAttachmentInReply = false
  private var mentionEta = false
  private var askForParking = false
  private var selectedAttachment = ""

  private var shareLiveLocation = true
  private var ringBell = false
  private var leavePhotoProof = true
  private var avoidStairs = false
  private var selectedSafePlace = ""
  private var deliveryNote = ""
  private var driverMessage = ""

  private var installPlan = ""
  private var updateWifiOnly = true
  private var backupBeforeRestart = true
  private var pauseBatterySaver = false
  private var backgroundRestart = false
  private var restartWindow = ""
  private var remindBeforeRestart = true
  private var closeBackgroundApps = false

  private var autoUpdateOnWifi = true
  private var openWhenDone = false
  private var notifyCompletion = true
  private var downloadBetaAssets = false
  private var changedPermissionLocation = true
  private var changedPermissionNearby = false
  private var changedPermissionNotifications = true
  private var changedPermissionCrashLogs = false

  private var reviewedRequesterIdentity = false
  private var understandProtectedSetting = false
  private var allowOnceOnly = true
  private var rememberDecision = false
  private var selectedApprovalScope = ""
  private var securityNote = ""

  private val currentScreen: String
    get() = backStack.lastOrNull() ?: SCREEN_GENERIC

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    binding = ActivityDestinationBinding.inflate(layoutInflater)
    setContentView(binding.root)

    binding.destinationBack.setOnClickListener { goBackOne() }
    onBackPressedDispatcher.addCallback(this) {
      goBackOne()
    }

    resetForTemplate(intent.getStringExtra(EXTRA_TEMPLATE).orEmpty())
  }

  override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    setIntent(intent)
    resetForTemplate(intent.getStringExtra(EXTRA_TEMPLATE).orEmpty())
  }

  private fun resetForTemplate(template: String) {
    resetState()
    backStack.clear()
    backStack.add(initialScreenFor(template))
    renderCurrentScreen()
  }

  private fun resetState() {
    notificationsEnabled = false
    notificationPopOnScreen = false
    notificationLockScreen = true
    categoryDirectMessages = true
    categoryMentions = true
    categoryReminders = false

    privacyAnalytics = true
    privacyPersonalized = false
    privacyMarketing = false
    privacyLocation = false
    vendorNewsDaily = true
    vendorAudienceLab = false
    vendorAdExchange = false
    vendorMeasurementStudio = false

    ratingStars = 0f
    reasonEaseOfUse = false
    reasonUseful = false
    reasonDesign = false
    reasonBugs = false
    reviewDraft = ""

    selectedDeal = ""
    filterPrimeOnly = true
    filterUnderFifty = false
    filterCarryOn = true
    filterFreeReturns = false
    selectedShipping = ""
    addProtectionPlan = false
    saveWishlist = false
    applyCoupon = false
    giftWrap = false
    selectedColor = ""
    selectedFulfillment = ""
    selectedPaymentMethod = ""

    replyDraft = ""
    includeAttachmentInReply = false
    mentionEta = false
    askForParking = false
    selectedAttachment = ""

    shareLiveLocation = true
    ringBell = false
    leavePhotoProof = true
    avoidStairs = false
    selectedSafePlace = ""
    deliveryNote = ""
    driverMessage = ""

    installPlan = ""
    updateWifiOnly = true
    backupBeforeRestart = true
    pauseBatterySaver = false
    backgroundRestart = false
    restartWindow = ""
    remindBeforeRestart = true
    closeBackgroundApps = false

    autoUpdateOnWifi = true
    openWhenDone = false
    notifyCompletion = true
    downloadBetaAssets = false
    changedPermissionLocation = true
    changedPermissionNearby = false
    changedPermissionNotifications = true
    changedPermissionCrashLogs = false

    reviewedRequesterIdentity = false
    understandProtectedSetting = false
    allowOnceOnly = true
    rememberDecision = false
    selectedApprovalScope = ""
    securityNote = ""
  }

  private fun renderCurrentScreen() {
    clearStatus()
    resetForm()
    when (currentScreen) {
      SCREEN_NOTIFICATION_SETTINGS -> renderNotificationSettings()
      SCREEN_NOTIFICATION_CATEGORIES -> renderNotificationCategories()
      SCREEN_NOTIFICATION_CONFIRMATION -> renderNotificationConfirmation()
      SCREEN_SYSTEM_UPDATE_SETTINGS -> renderSystemUpdateSettings()
      SCREEN_SYSTEM_UPDATE_CHANGELOG -> renderSystemUpdateChangelog()
      SCREEN_SYSTEM_UPDATE_DOWNLOAD -> renderSystemUpdateDownload()
      SCREEN_SYSTEM_UPDATE_RESTART -> renderSystemUpdateRestart()
      SCREEN_SYSTEM_UPDATE_CONFIRMED -> renderSystemUpdateConfirmed()
      SCREEN_APP_STORE_UPDATE -> renderAppStoreUpdate()
      SCREEN_APP_STORE_PERMISSIONS -> renderAppStorePermissions()
      SCREEN_APP_STORE_QUEUE -> renderAppStoreQueue()
      SCREEN_MESSAGE_THREAD -> renderMessageThread()
      SCREEN_MESSAGE_REPLY -> renderMessageReply()
      SCREEN_MESSAGE_ATTACHMENT -> renderMessageAttachment()
      SCREEN_MESSAGE_SENT -> renderMessageSent()
      SCREEN_DELIVERY_TRACKING -> renderDeliveryTracking()
      SCREEN_DELIVERY_MAP -> renderDeliveryMap()
      SCREEN_DELIVERY_SAFE_PLACE -> renderDeliverySafePlace()
      SCREEN_DELIVERY_CONTACT -> renderDeliveryContact()
      SCREEN_DELIVERY_CONFIRMATION -> renderDeliveryConfirmation()
      SCREEN_PRIVACY_OPTIONS -> renderPrivacyOptions()
      SCREEN_PRIVACY_VENDORS -> renderPrivacyVendors()
      SCREEN_PRIVACY_SUMMARY -> renderPrivacySummary()
      SCREEN_SECURITY_CENTER -> renderSecurityCenter()
      SCREEN_SECURITY_REVIEW -> renderSecurityReview()
      SCREEN_SECURITY_CONFIRMED -> renderSecurityConfirmed()
      SCREEN_RATING_FLOW -> renderRatingFlow()
      SCREEN_RATING_REVIEW -> renderRatingReview()
      SCREEN_RATING_CONFIRMATION -> renderRatingConfirmation()
      SCREEN_SHOPPING_AMAZON -> renderShoppingFeed()
      SCREEN_SHOPPING_DETAIL -> renderShoppingDetail()
      SCREEN_SHOPPING_COMPARE -> renderShoppingCompare()
      SCREEN_SHOPPING_CART -> renderShoppingCart()
      SCREEN_SHOPPING_CHECKOUT -> renderShoppingCheckout()
      SCREEN_SHOPPING_CONFIRMATION -> renderShoppingConfirmation()
      else -> renderGenericFallback()
    }
  }

  private fun renderNotificationSettings() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / Notifications / Android System",
      stepLabel = "Step 1 of 3",
      title = "Notification permissions",
      subtitle = "The allow flow now continues into real toggles instead of ending immediately.",
      body =
        "Android System notifications\n\n" +
          "Turn on the master notification switch first. Once alerts are allowed, " +
          "you can continue deeper into category-level controls.",
      primaryButton = "Review categories",
      secondaryButton = "Back to app",
    )
    setPanelHeader(
      "App notifications",
      "These switches mimic the permission handoff that usually happens after a permission prompt."
    )
    showSwitchPanel(
      optionOne = "Allow notifications" to notificationsEnabled,
      optionTwo = "Pop on screen" to notificationPopOnScreen,
      optionThree = "Show on lock screen" to notificationLockScreen,
    )
    setSummaryFooter(
      if (notificationsEnabled) {
        "Notifications are enabled. Continue to configure specific channels."
      } else {
        "Enable notifications to unlock the next settings page."
      }
    )
    setActionButtons(
      primaryLabel = "Review categories",
      onPrimary = {
        captureNotificationSwitches()
        if (!notificationsEnabled) {
          showStatus("Turn on Allow notifications before continuing.")
        } else {
          navigateTo(SCREEN_NOTIFICATION_CATEGORIES)
        }
      },
      secondaryLabel = "Back to app",
      onSecondary = { finish() },
    )
  }

  private fun renderNotificationCategories() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / Notifications / Android System / Categories",
      stepLabel = "Step 2 of 3",
      title = "Notification categories",
      subtitle = "After permission grant, the user now has to manage channel-level behavior too.",
      body =
        "Fine-tune what gets through once the master switch is on. " +
          "Different categories can still interrupt the original task in different ways.",
      primaryButton = "Save settings",
      secondaryButton = "Back",
    )
    setPanelHeader(
      "Choose categories",
      "Leave at least one category active if you still want alerts to arrive."
    )
    showSwitchPanel(
      optionOne = "Direct messages" to categoryDirectMessages,
      optionTwo = "Mentions and reactions" to categoryMentions,
      optionThree = "System reminders" to categoryReminders,
    )
    setSummaryFooter("Enabled categories: ${enabledNotificationCategories().ifBlank { "None" }}")
    setActionButtons(
      primaryLabel = "Save settings",
      onPrimary = {
        captureNotificationCategories()
        navigateTo(SCREEN_NOTIFICATION_CONFIRMATION)
      },
      secondaryLabel = "Back",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderNotificationConfirmation() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / Notifications / Android System / Summary",
      stepLabel = "Step 3 of 3",
      title = "Notifications updated",
      subtitle = "The permission flow now ends only after a second settings screen is handled.",
      body =
        "Allow notifications: ${yesNo(notificationsEnabled)}\n" +
          "Pop on screen: ${yesNo(notificationPopOnScreen)}\n" +
          "Lock screen: ${yesNo(notificationLockScreen)}\n\n" +
          "Categories kept on:\n${enabledNotificationCategories().ifBlank { "• None" }}",
      primaryButton = "Done",
      secondaryButton = "Edit categories",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Edit categories",
      onSecondary = {
        restartFlowAt(SCREEN_NOTIFICATION_SETTINGS)
      },
    )
  }

  private fun renderSystemUpdateSettings() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / System / System update",
      stepLabel = "Step 1 of 4",
      title = "System update",
      subtitle = "System updates now branch into planning, download, and restart scheduling.",
      body =
        "Security patch level: October 2023\n\n" +
          "Update available\n" +
          "• Security fixes\n" +
          "• Stability improvements\n" +
          "• Restart required after install",
      primaryButton = "Continue update",
      secondaryButton = "View changelog",
    )
    setPanelHeader(
      "Install plan",
      "Pick when the device should handle the update before the download can continue."
    )
    showRadioPanel(
      optionOne = "Download now over Wi-Fi",
      optionTwo = "Install tonight at 2:00 AM",
      optionThree = "Install on next idle charge",
      selectedValue = installPlan,
    )
    showCheckboxPanel(
      optionOne = "Back up before restart" to backupBeforeRestart,
      optionTwo = "Use Wi-Fi only" to updateWifiOnly,
      optionThree = "Pause battery saver during install" to pauseBatterySaver,
      optionFour = "Allow background restart when idle" to backgroundRestart,
    )
    setSummaryFooter("Current install plan: ${installPlan.ifBlank { "Not selected" }}")
    setActionButtons(
      primaryLabel = "Continue update",
      onPrimary = {
        captureUpdatePlan()
        if (installPlan.isBlank()) {
          showStatus("Select an install plan before continuing.")
        } else {
          navigateTo(SCREEN_SYSTEM_UPDATE_DOWNLOAD)
        }
      },
      secondaryLabel = "View changelog",
      onSecondary = {
        captureUpdatePlan()
        navigateTo(SCREEN_SYSTEM_UPDATE_CHANGELOG)
      },
    )
  }

  private fun renderSystemUpdateChangelog() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / System / System update / Changelog",
      stepLabel = "Step 2 of 4",
      title = "What changed",
      subtitle = "The update flow can now detour through release notes before the download begins.",
      body =
        "Highlights\n\n" +
          "• Security patch for background services\n" +
          "• Improved gesture responsiveness\n" +
          "• Lower idle battery drain\n\n" +
          "Restart will be required to finish installation.",
      primaryButton = "Start download",
      secondaryButton = "Back",
    )
    showQuickActions(
      firstLabel = "Security fixes",
      onFirst = { showStatus("Release notes focused on security hardening were expanded.") },
      secondLabel = "Stability details",
      onSecond = { showStatus("Stability changes include launcher, audio, and network fixes.") },
      thirdLabel = "Restart notes",
      onThird = { showStatus("A restart will be required after the package is verified.") },
    )
    setSummaryFooter("Chosen install plan: ${installPlan.ifBlank { "Not selected yet" }}")
    setActionButtons(
      primaryLabel = "Start download",
      onPrimary = { navigateTo(SCREEN_SYSTEM_UPDATE_DOWNLOAD) },
      secondaryLabel = "Back",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderSystemUpdateDownload() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / System / System update / Download",
      stepLabel = "Step 3 of 4",
      title = "Downloading update",
      subtitle = "The agent now has to move past a progress state before the flow ends.",
      body =
        "Package verification is in progress.\n\n" +
          "Network conditions and restart timing can still change the path from here.",
      primaryButton = "Schedule restart",
      secondaryButton = "Pause download",
    )
    setPanelHeader("Download status", "Installation cannot finish until restart timing is confirmed.")
    showProgressPanel(progress = 62, caption = "1.2 GB of 1.9 GB downloaded over Wi-Fi")
    showCheckboxPanel(
      optionOne = "Use Wi-Fi only" to updateWifiOnly,
      optionTwo = "Resume automatically on reconnect" to true,
      optionThree = "Notify when ready to restart" to remindBeforeRestart,
      optionFour = "Delete installer after completion" to false,
    )
    setSummaryFooter("Install plan: $installPlan")
    setActionButtons(
      primaryLabel = "Schedule restart",
      onPrimary = {
        captureDownloadOptions()
        navigateTo(SCREEN_SYSTEM_UPDATE_RESTART)
      },
      secondaryLabel = "Pause download",
      onSecondary = {
        captureDownloadOptions()
        showStatus("Download paused at 62%. Resume it before the restart can be scheduled.")
      },
    )
  }

  private fun renderSystemUpdateRestart() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / System / System update / Restart",
      stepLabel = "Step 4 of 4",
      title = "Schedule restart",
      subtitle = "A third screen is now needed before the update flow can resolve.",
      body =
        "The update package is ready. Pick a restart window so the installation can complete.",
      primaryButton = "Confirm restart",
      secondaryButton = "Remind me later",
    )
    setPanelHeader("Restart window", "Choose when the device may restart to finish installing.")
    showRadioPanel(
      optionOne = "Tonight at 2:00 AM",
      optionTwo = "Tonight at 3:30 AM",
      optionThree = "When charging and idle",
      selectedValue = restartWindow,
    )
    showCheckboxPanel(
      optionOne = "Remind me 10 minutes before restart" to remindBeforeRestart,
      optionTwo = "Close background apps automatically" to closeBackgroundApps,
      optionThree = "Keep alarms active" to true,
      optionFour = "" to false,
    )
    setActionButtons(
      primaryLabel = "Confirm restart",
      onPrimary = {
        captureRestartOptions()
        if (restartWindow.isBlank()) {
          showStatus("Choose a restart window before confirming.")
        } else {
          navigateTo(SCREEN_SYSTEM_UPDATE_CONFIRMED)
        }
      },
      secondaryLabel = "Remind me later",
      onSecondary = {
        captureRestartOptions()
        showStatus("Restart was deferred. The update flow remains unresolved.")
      },
    )
  }

  private fun renderSystemUpdateConfirmed() {
    bindCommon(
      appName = "Settings",
      pathLabel = "Settings / System / System update / Summary",
      stepLabel = "Scheduled",
      title = "Restart scheduled",
      subtitle = "This update perturbation now resolves only after multiple pages are handled.",
      body =
        "Restart time: $restartWindow\n" +
          "Wi-Fi only: ${yesNo(updateWifiOnly)}\n" +
          "Back up before restart: ${yesNo(backupBeforeRestart)}\n" +
          "Reminder enabled: ${yesNo(remindBeforeRestart)}",
      primaryButton = "Done",
      secondaryButton = "Edit plan",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Edit plan",
      onSecondary = { restartFlowAt(SCREEN_SYSTEM_UPDATE_SETTINGS) },
    )
  }

  private fun renderAppStoreUpdate() {
    bindCommon(
      appName = "App Store",
      pathLabel = "App Store / Available updates / Maps Go",
      stepLabel = "Step 1 of 3",
      title = "Maps Go update",
      subtitle = "The store-style detour now has a permissions review and download queue.",
      body =
        "What's new\n\n" +
          "• Route previews\n" +
          "• Battery optimizations\n" +
          "• Bug fixes\n\n" +
          "Reviews mention improved offline navigation and better rerouting.",
      primaryButton = "Review permissions",
      secondaryButton = "View update queue",
    )
    setPanelHeader("Update preferences", "Store flows often add extra consent and queue management steps.")
    showCheckboxPanel(
      optionOne = "Auto-update on Wi-Fi" to autoUpdateOnWifi,
      optionTwo = "Open app when update finishes" to openWhenDone,
      optionThree = "Notify when installation completes" to notifyCompletion,
      optionFour = "Download extra beta assets" to downloadBetaAssets,
    )
    setActionButtons(
      primaryLabel = "Review permissions",
      onPrimary = {
        captureAppStorePreferences()
        navigateTo(SCREEN_APP_STORE_PERMISSIONS)
      },
      secondaryLabel = "View update queue",
      onSecondary = {
        captureAppStorePreferences()
        navigateTo(SCREEN_APP_STORE_QUEUE)
      },
    )
  }

  private fun renderAppStorePermissions() {
    bindCommon(
      appName = "App Store",
      pathLabel = "App Store / Maps Go / Permission changes",
      stepLabel = "Step 2 of 3",
      title = "Review update permissions",
      subtitle = "The user now has to inspect permission changes before the install can proceed.",
      body =
        "This update requests a few changed capabilities. Review what the app will access after updating.",
      primaryButton = "Continue update",
      secondaryButton = "Back",
    )
    setPanelHeader("Changed access", "These items are displayed like a store-side data safety review.")
    showCheckboxPanel(
      optionOne = "Approximate location access" to changedPermissionLocation,
      optionTwo = "Nearby devices detection" to changedPermissionNearby,
      optionThree = "Notification posting" to changedPermissionNotifications,
      optionFour = "Crash and diagnostics logs" to changedPermissionCrashLogs,
    )
    setSummaryFooter("Auto-update on Wi-Fi: ${yesNo(autoUpdateOnWifi)}")
    setActionButtons(
      primaryLabel = "Continue update",
      onPrimary = {
        captureAppStorePermissions()
        navigateTo(SCREEN_APP_STORE_QUEUE)
      },
      secondaryLabel = "Back",
      onSecondary = {
        captureAppStorePermissions()
        goBackOne()
      },
    )
  }

  private fun renderAppStoreQueue() {
    bindCommon(
      appName = "App Store",
      pathLabel = "App Store / Downloads / Queue",
      stepLabel = "Step 3 of 3",
      title = "Update queue",
      subtitle = "The store path now ends in a queue-management page instead of a single tap.",
      body =
        "Maps Go is queued behind two other downloads.\n\n" +
          "• Transit Planner\n" +
          "• City Weather\n" +
          "• Maps Go",
      primaryButton = "Done",
      secondaryButton = "Reorder queue",
    )
    setPanelHeader("Download progress", "The update queue can still compete for attention after consent.")
    showProgressPanel(progress = 41, caption = "Maps Go will begin after 2 queued updates finish")
    setSummaryFooter("Open app when done: ${yesNo(openWhenDone)}")
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Reorder queue",
      onSecondary = { showStatus("Queue reordered. Maps Go moved behind Transit Planner.") },
    )
  }

  private fun renderMessageThread() {
    bindCommon(
      appName = "Messages",
      pathLabel = "Messages / Jordan",
      stepLabel = "Step 1 of 4",
      title = "Jordan",
      subtitle = "Replying now opens a composer and optional attachment step.",
      body =
        "Jordan\n" +
          "The meeting moved to 3:30 PM.\n\n" +
          "Unread attachments:\n" +
          "• agenda.pdf\n" +
          "• parking_map.png\n\n" +
          "Last message sent 4 minutes ago.",
      primaryButton = "Reply",
      secondaryButton = "Mark unread",
    )
    setPanelHeader("Quick actions", "Attachments and thread actions now create more branching before completion.")
    showQuickActions(
      firstLabel = "Preview agenda.pdf",
      onFirst = { showStatus("Agenda preview opened in a sheet above the thread.") },
      secondLabel = "Open parking_map.png",
      onSecond = { showStatus("Parking map preview opened. Return to the thread to keep replying.") },
      thirdLabel = "View earlier messages",
      onThird = { showStatus("Three earlier messages loaded into the thread.") },
    )
    setActionButtons(
      primaryLabel = "Reply",
      onPrimary = { navigateTo(SCREEN_MESSAGE_REPLY) },
      secondaryLabel = "Mark unread",
      onSecondary = { showStatus("Thread marked unread, but the conversation view is still open.") },
    )
  }

  private fun renderMessageReply() {
    bindCommon(
      appName = "Messages",
      pathLabel = "Messages / Jordan / Reply",
      stepLabel = "Step 2 of 4",
      title = "Compose reply",
      subtitle = "The incoming-message perturbation now requires a real reply action chain.",
      body =
        "Draft a response, optionally add context, and then decide whether to attach a file before sending.",
      primaryButton = "Send reply",
      secondaryButton = "Attach file",
    )
    setPanelHeader("Reply draft", "Quick replies can prefill the composer, but you still need to send the message.")
    showQuickActions(
      firstLabel = "Sounds good, thanks",
      onFirst = { applyReplyTemplate("Sounds good, thanks.") },
      secondLabel = "I'll be there at 3:30",
      onSecond = { applyReplyTemplate("I will be there at 3:30 PM.") },
      thirdLabel = "Can we move it again?",
      onThird = { applyReplyTemplate("Can we move it again if parking is full?") },
    )
    showCheckboxPanel(
      optionOne = "Attach latest agenda" to includeAttachmentInReply,
      optionTwo = "Mention arrival ETA" to mentionEta,
      optionThree = "Ask about parking" to askForParking,
      optionFour = "" to false,
    )
    showInputPanel("Type a reply to Jordan", replyDraft)
    setSummaryFooter(
      if (replyDraft.isBlank()) {
        "No reply drafted yet."
      } else {
        "Current draft: $replyDraft"
      }
    )
    setActionButtons(
      primaryLabel = "Send reply",
      onPrimary = {
        captureMessageReply()
        if (replyDraft.isBlank()) {
          showStatus("Type a reply or choose a quick-reply suggestion first.")
        } else {
          navigateTo(SCREEN_MESSAGE_SENT)
        }
      },
      secondaryLabel = "Attach file",
      onSecondary = {
        captureMessageReply()
        navigateTo(SCREEN_MESSAGE_ATTACHMENT)
      },
    )
  }

  private fun renderMessageAttachment() {
    bindCommon(
      appName = "Messages",
      pathLabel = "Messages / Jordan / Attachments",
      stepLabel = "Step 3 of 4",
      title = "Choose attachment",
      subtitle = "Replying can now branch into a file-picker style step before the send completes.",
      body =
        "Select one attachment to include with the reply. The draft text will be preserved when you continue.",
      primaryButton = "Attach and send",
      secondaryButton = "Back to draft",
    )
    setPanelHeader("Available files", "This mimics the extra work of selecting supporting context before sending.")
    showRadioPanel(
      optionOne = "agenda.pdf",
      optionTwo = "parking_map.png",
      optionThree = "voice_note.m4a",
      selectedValue = selectedAttachment,
    )
    setSummaryFooter("Draft kept: ${replyDraft.ifBlank { "No draft yet" }}")
    setActionButtons(
      primaryLabel = "Attach and send",
      onPrimary = {
        selectedAttachment = currentRadioSelection()
        if (selectedAttachment.isBlank()) {
          showStatus("Select an attachment before sending.")
        } else {
          includeAttachmentInReply = true
          navigateTo(SCREEN_MESSAGE_SENT)
        }
      },
      secondaryLabel = "Back to draft",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderMessageSent() {
    bindCommon(
      appName = "Messages",
      pathLabel = "Messages / Jordan / Sent",
      stepLabel = "Step 4 of 4",
      title = "Reply sent",
      subtitle = "The message interruption now resolves only after a proper compose path.",
      body =
        "Reply: ${replyDraft.ifBlank { "No text drafted" }}\n" +
          "Attachment included: ${if (includeAttachmentInReply) selectedAttachment.ifBlank { "Yes" } else "No"}\n" +
          "Mention ETA: ${yesNo(mentionEta)}\n" +
          "Asked about parking: ${yesNo(askForParking)}",
      primaryButton = "Done",
      secondaryButton = "Reply again",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Reply again",
      onSecondary = { restartFlowAt(SCREEN_MESSAGE_THREAD) },
    )
  }

  private fun renderDeliveryTracking() {
    bindCommon(
      appName = "Parcel Tracker",
      pathLabel = "Parcel Tracker / Delivery / Order #4419",
      stepLabel = "Step 1 of 4",
      title = "Driver is nearby",
      subtitle = "Delivery alerts now branch into tracking, map, and safe-place configuration.",
      body =
        "Current stop: 2 deliveries away\n\n" +
          "Timeline\n" +
          "• Sorted at facility\n" +
          "• Out for delivery\n" +
          "• Driver is nearby",
      primaryButton = "Open map",
      secondaryButton = "Delivery options",
    )
    setPanelHeader("Progress", "The alert now continues into a map and instruction workflow.")
    showProgressPanel(progress = 78, caption = "ETA 8 minutes. Driver is 1.1 miles away.")
    setActionButtons(
      primaryLabel = "Open map",
      onPrimary = { navigateTo(SCREEN_DELIVERY_MAP) },
      secondaryLabel = "Delivery options",
      onSecondary = { navigateTo(SCREEN_DELIVERY_SAFE_PLACE) },
    )
  }

  private fun renderDeliveryMap() {
    bindCommon(
      appName = "Parcel Tracker",
      pathLabel = "Parcel Tracker / Delivery / Live map",
      stepLabel = "Step 2 of 4",
      title = "Driver route",
      subtitle = "Open map now goes to a dedicated map-style page instead of ending on the tracking card.",
      body =
        "Follow the driver in real time, then decide whether you need to call, share notes, or change the drop-off point.",
      primaryButton = "Choose safe place",
      secondaryButton = "Call driver",
    )
    setPanelHeader("Live route", "The delivery flow now detours through a map page before it can resolve.")
    showMapPanel(
      canvasLabel = "Map preview\n\nDriver is 2 blocks away\nBlue route highlighted to your address",
      metaLabel = "Next turn: East on Cedar Ave\nBuilding access note: Use side gate after 3 PM",
    )
    showCheckboxPanel(
      optionOne = "Share live location with driver" to shareLiveLocation,
      optionTwo = "Ring bell on arrival" to ringBell,
      optionThree = "Require photo proof" to leavePhotoProof,
      optionFour = "Avoid stairs / use ramp" to avoidStairs,
    )
    setActionButtons(
      primaryLabel = "Choose safe place",
      onPrimary = {
        captureDeliveryMapOptions()
        navigateTo(SCREEN_DELIVERY_SAFE_PLACE)
      },
      secondaryLabel = "Call driver",
      onSecondary = {
        captureDeliveryMapOptions()
        navigateTo(SCREEN_DELIVERY_CONTACT)
      },
    )
  }

  private fun renderDeliverySafePlace() {
    bindCommon(
      appName = "Parcel Tracker",
      pathLabel = "Parcel Tracker / Delivery / Safe place",
      stepLabel = "Step 3 of 4",
      title = "Safe place instructions",
      subtitle = "The delivery alert now needs a placement choice before it can finish.",
      body =
        "Pick where the package should be left if you cannot meet the driver at the door.",
      primaryButton = "Save instructions",
      secondaryButton = "Back to map",
    )
    setPanelHeader("Drop-off location", "This selection feeds the final delivery summary.")
    showRadioPanel(
      optionOne = "Front porch",
      optionTwo = "Side gate",
      optionThree = "Reception desk",
      selectedValue = selectedSafePlace,
    )
    showInputPanel("Optional note for the driver", deliveryNote)
    setSummaryFooter("Current safe place: ${selectedSafePlace.ifBlank { "Not selected" }}")
    setActionButtons(
      primaryLabel = "Save instructions",
      onPrimary = {
        captureDeliverySafePlace()
        if (selectedSafePlace.isBlank()) {
          showStatus("Choose a safe place before saving.")
        } else {
          navigateTo(SCREEN_DELIVERY_CONFIRMATION)
        }
      },
      secondaryLabel = "Back to map",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderDeliveryContact() {
    bindCommon(
      appName = "Parcel Tracker",
      pathLabel = "Parcel Tracker / Delivery / Contact driver",
      stepLabel = "Step 3 of 4",
      title = "Message driver",
      subtitle = "The map flow can now branch into a driver contact page too.",
      body =
        "Send a quick note if the access point is tricky or if you need extra handoff instructions.",
      primaryButton = "Send note",
      secondaryButton = "Back to map",
    )
    setPanelHeader("Quick messages", "Use a canned message or write your own before returning to delivery.")
    showQuickActions(
      firstLabel = "Use side gate",
      onFirst = { applyDriverTemplate("Please use the side gate when you arrive.") },
      secondLabel = "Wait 2 minutes",
      onSecond = { applyDriverTemplate("Please wait 2 minutes; I am on my way downstairs.") },
      thirdLabel = "Leave at reception",
      onThird = { applyDriverTemplate("If no one answers, please leave the package at reception.") },
    )
    showInputPanel("Write a note for the driver", driverMessage)
    setActionButtons(
      primaryLabel = "Send note",
      onPrimary = {
        driverMessage = binding.destinationInput.text?.toString()?.trim().orEmpty()
        if (driverMessage.isBlank()) {
          showStatus("Enter a note or choose a quick message first.")
        } else {
          navigateTo(SCREEN_DELIVERY_CONFIRMATION)
        }
      },
      secondaryLabel = "Back to map",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderDeliveryConfirmation() {
    bindCommon(
      appName = "Parcel Tracker",
      pathLabel = "Parcel Tracker / Delivery / Summary",
      stepLabel = "Step 4 of 4",
      title = "Delivery instructions saved",
      subtitle = "The delivery alert now requires map and instruction handling before it resolves.",
      body =
        "Safe place: ${selectedSafePlace.ifBlank { "Not selected" }}\n" +
          "Driver note: ${deliveryNote.ifBlank { driverMessage.ifBlank { "None" } }}\n" +
          "Share live location: ${yesNo(shareLiveLocation)}\n" +
          "Require photo proof: ${yesNo(leavePhotoProof)}",
      primaryButton = "Done",
      secondaryButton = "Edit instructions",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Edit instructions",
      onSecondary = { restartFlowAt(SCREEN_DELIVERY_TRACKING) },
    )
  }

  private fun renderPrivacyOptions() {
    bindCommon(
      appName = "News Daily",
      pathLabel = "News Daily / Privacy choices",
      stepLabel = "Step 1 of 3",
      title = "Manage privacy options",
      subtitle = "The consent sheet now contains real selectable options instead of a passive list.",
      body =
        "Choose which purposes you want to keep active while using the app. " +
          "Vendor access is handled on the next page.",
      primaryButton = "Review vendors",
      secondaryButton = "Reject all",
    )
    setPanelHeader("Purpose controls", "Each purpose can now be accepted or declined independently.")
    showCheckboxPanel(
      optionOne = "Analytics cookies" to privacyAnalytics,
      optionTwo = "Personalized content" to privacyPersonalized,
      optionThree = "Marketing identifiers" to privacyMarketing,
      optionFour = "Precise location personalization" to privacyLocation,
    )
    setSummaryFooter("Enabled purposes: ${enabledPurposesSummary()}")
    setActionButtons(
      primaryLabel = "Review vendors",
      onPrimary = {
        capturePrivacyPurposes()
        navigateTo(SCREEN_PRIVACY_VENDORS)
      },
      secondaryLabel = "Reject all",
      onSecondary = {
        privacyAnalytics = false
        privacyPersonalized = false
        privacyMarketing = false
        privacyLocation = false
        vendorNewsDaily = false
        vendorAudienceLab = false
        vendorAdExchange = false
        vendorMeasurementStudio = false
        navigateTo(SCREEN_PRIVACY_SUMMARY)
      },
    )
  }

  private fun renderPrivacyVendors() {
    bindCommon(
      appName = "News Daily",
      pathLabel = "News Daily / Privacy choices / Vendors",
      stepLabel = "Step 2 of 3",
      title = "Vendor access",
      subtitle = "Managing options now goes one screen deeper into partner-level controls.",
      body =
        "Choose which vendors can still receive consent signals for the purposes you kept on.",
      primaryButton = "Save choices",
      secondaryButton = "Back",
    )
    setPanelHeader("Vendor permissions", "These switches stay separate from the purpose-level choices.")
    showCheckboxPanel(
      optionOne = "News Daily first-party personalization" to vendorNewsDaily,
      optionTwo = "Audience Lab analytics" to vendorAudienceLab,
      optionThree = "Ad Exchange marketplace" to vendorAdExchange,
      optionFour = "Measurement Studio reporting" to vendorMeasurementStudio,
    )
    setSummaryFooter("Enabled vendors: ${enabledVendorsSummary()}")
    setActionButtons(
      primaryLabel = "Save choices",
      onPrimary = {
        capturePrivacyVendors()
        navigateTo(SCREEN_PRIVACY_SUMMARY)
      },
      secondaryLabel = "Back",
      onSecondary = {
        capturePrivacyVendors()
        goBackOne()
      },
    )
  }

  private fun renderPrivacySummary() {
    bindCommon(
      appName = "News Daily",
      pathLabel = "News Daily / Privacy choices / Summary",
      stepLabel = "Step 3 of 3",
      title = "Privacy choices saved",
      subtitle = "The consent perturbation now takes multiple steps and includes real option selection.",
      body =
        "Purposes enabled:\n${enabledPurposesSummary()}\n\n" +
          "Vendors enabled:\n${enabledVendorsSummary()}",
      primaryButton = "Done",
      secondaryButton = "Edit choices",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Edit choices",
      onSecondary = { restartFlowAt(SCREEN_PRIVACY_OPTIONS) },
    )
  }

  private fun renderSecurityCenter() {
    bindCommon(
      appName = "Security Center",
      pathLabel = "Security Center / Review action",
      stepLabel = "Step 1 of 3",
      title = "Protected action review",
      subtitle = "Security prompts now include a verification checklist before approval is possible.",
      body =
        "Risk summary\n" +
          "• App requested a protected setting\n" +
          "• Verify requester identity\n" +
          "• Confirm before continuing",
      primaryButton = "Continue review",
      secondaryButton = "Cancel",
    )
    setPanelHeader("Verification checklist", "Both identity and scope should be reviewed before proceeding.")
    showCheckboxPanel(
      optionOne = "I reviewed the requester identity" to reviewedRequesterIdentity,
      optionTwo = "I understand this changes a protected setting" to understandProtectedSetting,
      optionThree = "Allow only once" to allowOnceOnly,
      optionFour = "Remember my decision for this app" to rememberDecision,
    )
    setActionButtons(
      primaryLabel = "Continue review",
      onPrimary = {
        captureSecurityChecklist()
        if (!reviewedRequesterIdentity || !understandProtectedSetting) {
          showStatus("Confirm the first two review items before continuing.")
        } else {
          navigateTo(SCREEN_SECURITY_REVIEW)
        }
      },
      secondaryLabel = "Cancel",
      onSecondary = { finish() },
    )
  }

  private fun renderSecurityReview() {
    bindCommon(
      appName = "Security Center",
      pathLabel = "Security Center / Review action / Scope",
      stepLabel = "Step 2 of 3",
      title = "Approval scope",
      subtitle = "The security flow now asks how broad the approval should be.",
      body =
        "Pick how far this approval should go, then optionally leave an audit note.",
      primaryButton = "Approve",
      secondaryButton = "Back",
    )
    setPanelHeader("Approval scope", "Protected actions often include another choice after the warning itself.")
    showRadioPanel(
      optionOne = "Allow once",
      optionTwo = "Allow while using the app",
      optionThree = "Always allow for this app",
      selectedValue = selectedApprovalScope,
    )
    showInputPanel("Optional audit note", securityNote)
    setActionButtons(
      primaryLabel = "Approve",
      onPrimary = {
        selectedApprovalScope = currentRadioSelection()
        securityNote = binding.destinationInput.text?.toString()?.trim().orEmpty()
        if (selectedApprovalScope.isBlank()) {
          showStatus("Choose an approval scope before approving.")
        } else {
          navigateTo(SCREEN_SECURITY_CONFIRMED)
        }
      },
      secondaryLabel = "Back",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderSecurityConfirmed() {
    bindCommon(
      appName = "Security Center",
      pathLabel = "Security Center / Review action / Summary",
      stepLabel = "Step 3 of 3",
      title = "Approval recorded",
      subtitle = "The security perturbation now ends after a multi-screen approval path.",
      body =
        "Scope: $selectedApprovalScope\n" +
          "Remember decision: ${yesNo(rememberDecision)}\n" +
          "Audit note: ${securityNote.ifBlank { "None" }}",
      primaryButton = "Done",
      secondaryButton = "Edit",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Edit",
      onSecondary = { restartFlowAt(SCREEN_SECURITY_CENTER) },
    )
  }

  private fun renderRatingFlow() {
    bindCommon(
      appName = "Notes Pro",
      pathLabel = "Notes Pro / Rate this app",
      stepLabel = "Step 1 of 3",
      title = "Rate this app",
      subtitle = "The rating flow now starts with an actual star selection page instead of an error.",
      body =
        "Choose a star rating first. Once a rating is selected, the review form will open on the next step.",
      primaryButton = "Write review",
      secondaryButton = "Not now",
    )
    setPanelHeader("Star rating", "This page behaves like the first stage of a real in-app rating flow.")
    showRatingPanel(ratingStars)
    setSummaryFooter(
      if (ratingStars > 0f) {
        "Selected rating: ${ratingStars.toInt()} star(s)"
      } else {
        "No rating selected yet."
      }
    )
    setActionButtons(
      primaryLabel = "Write review",
      onPrimary = {
        captureRatingValue()
        if (ratingStars <= 0f) {
          showStatus("Select a star rating before continuing.")
        } else {
          navigateTo(SCREEN_RATING_REVIEW)
        }
      },
      secondaryLabel = "Not now",
      onSecondary = { finish() },
    )
  }

  private fun renderRatingReview() {
    bindCommon(
      appName = "Notes Pro",
      pathLabel = "Notes Pro / Rate this app / Review",
      stepLabel = "Step 2 of 3",
      title = "Write a review",
      subtitle = "A second review form now follows the star selection step.",
      body =
        "Share what stood out, what should improve, or what convinced you to rate the app this way.",
      primaryButton = "Submit review",
      secondaryButton = "Skip comment",
    )
    setPanelHeader("Review details", "Suggested prompts and comment entry now make the rating flow multi-step.")
    showRatingPanel(ratingStars)
    showCheckboxPanel(
      optionOne = "Easy to use" to reasonEaseOfUse,
      optionTwo = "Helpful features" to reasonUseful,
      optionThree = "Clean design" to reasonDesign,
      optionFour = "Needs bug fixes" to reasonBugs,
    )
    showQuickActions(
      firstLabel = "Fast and simple",
      onFirst = { applyReviewTemplate("Fast and simple to use.") },
      secondLabel = "Helpful reminders",
      onSecond = { applyReviewTemplate("The reminders and note organization are really helpful.") },
      thirdLabel = "Needs polish",
      onThird = { applyReviewTemplate("Useful app, but a few rough edges still need polish.") },
    )
    showInputPanel("Tell us more about your experience", reviewDraft)
    setSummaryFooter("Selected stars: ${ratingStars.toInt()}  Reason tags: ${enabledReviewReasons()}")
    setActionButtons(
      primaryLabel = "Submit review",
      onPrimary = {
        captureReviewDetails()
        navigateTo(SCREEN_RATING_CONFIRMATION)
      },
      secondaryLabel = "Skip comment",
      onSecondary = {
        captureReviewDetails()
        navigateTo(SCREEN_RATING_CONFIRMATION)
      },
    )
  }

  private fun renderRatingConfirmation() {
    bindCommon(
      appName = "Notes Pro",
      pathLabel = "Notes Pro / Rate this app / Summary",
      stepLabel = "Step 3 of 3",
      title = "Thanks for the feedback",
      subtitle = "The rating perturbation now completes through a full review path.",
      body =
        "Rating: ${ratingStars.toInt()} star(s)\n" +
          "Reasons: ${enabledReviewReasons()}\n" +
          "Comment: ${reviewDraft.ifBlank { "No comment submitted" }}",
      primaryButton = "Done",
      secondaryButton = "Edit review",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Edit review",
      onSecondary = { restartFlowAt(SCREEN_RATING_FLOW) },
    )
  }

  private fun renderShoppingFeed() {
    bindCommon(
      appName = "Amazon Shopping",
      pathLabel = "Home / Deals / Travel gear",
      stepLabel = "Step 1 of 5",
      title = "48-hour flash sale",
      subtitle = "The flash-sale detour now turns into a multi-screen shopping flow.",
      body =
        "Prime members are seeing extra travel gear discounts today.\n\n" +
          "Choose a deal, adjust filters, and then inspect the product before it reaches your cart.",
      primaryButton = "View selected deal",
      secondaryButton = "Apply filters",
    )
    setPanelHeader("Featured deals", "Selecting a product is now only the first step in the shopping detour.")
    showRadioPanel(
      optionOne = "Hiking backpack 60% off",
      optionTwo = "Packing cubes bundle",
      optionThree = "Carry-on organizer with Prime badge",
      selectedValue = selectedDeal,
    )
    showCheckboxPanel(
      optionOne = "Prime only" to filterPrimeOnly,
      optionTwo = "Under $50" to filterUnderFifty,
      optionThree = "Carry-on size" to filterCarryOn,
      optionFour = "Free returns" to filterFreeReturns,
    )
    setSummaryFooter("Selected deal: ${selectedDeal.ifBlank { "None" }}")
    setActionButtons(
      primaryLabel = "View selected deal",
      onPrimary = {
        captureShoppingFeed()
        if (selectedDeal.isBlank()) {
          showStatus("Pick a travel deal before opening the product page.")
        } else {
          navigateTo(SCREEN_SHOPPING_DETAIL)
        }
      },
      secondaryLabel = "Apply filters",
      onSecondary = {
        captureShoppingFeed()
        if (!filterPrimeOnly && !filterUnderFifty && !filterCarryOn && !filterFreeReturns) {
          showStatus("Toggle at least one filter to refresh the flash-sale feed.")
        } else {
          showStatus("Flash-sale feed refreshed with your selected filters.")
        }
      },
    )
  }

  private fun renderShoppingDetail() {
    val dealName = selectedDeal.ifBlank { "Carry-on organizer with Prime badge" }
    bindCommon(
      appName = "Amazon Shopping",
      pathLabel = "Home / Deals / Travel gear / Item",
      stepLabel = "Step 2 of 5",
      title = dealName,
      subtitle = "The second page now includes shipping, coupons, and other product-level decisions.",
      body =
        "$dealName\n\n" +
          "Sponsored options, add-ons, and shipping choices all compete for attention before the cart step.",
      primaryButton = "Add to cart",
      secondaryButton = "Compare colors",
    )
    setPanelHeader("Purchase options", "Choose a shipping speed before you can add the item to the cart.")
    showRadioPanel(
      optionOne = "Standard delivery - Thursday",
      optionTwo = "Two-day delivery - Tuesday",
      optionThree = "Overnight delivery - Tomorrow morning",
      selectedValue = selectedShipping,
    )
    showCheckboxPanel(
      optionOne = "Add 2-year protection plan" to addProtectionPlan,
      optionTwo = "Save to wishlist too" to saveWishlist,
      optionThree = "Apply extra 10% coupon" to applyCoupon,
      optionFour = "Gift wrap this item" to giftWrap,
    )
    setSummaryFooter("Selected shipping: ${selectedShipping.ifBlank { "Not selected" }}")
    setActionButtons(
      primaryLabel = "Add to cart",
      onPrimary = {
        captureShoppingDetail()
        if (selectedShipping.isBlank()) {
          showStatus("Choose a shipping speed before adding the item to the cart.")
        } else {
          navigateTo(SCREEN_SHOPPING_CART)
        }
      },
      secondaryLabel = "Compare colors",
      onSecondary = {
        captureShoppingDetail()
        navigateTo(SCREEN_SHOPPING_COMPARE)
      },
    )
  }

  private fun renderShoppingCompare() {
    bindCommon(
      appName = "Amazon Shopping",
      pathLabel = "Home / Deals / Travel gear / Compare finishes",
      stepLabel = "Step 3 of 5",
      title = "Compare finishes",
      subtitle = "The flash-sale flow now adds another product decision before the cart.",
      body =
        "Compare traveler reviews, in-stock finishes, and photo uploads before deciding which variant to buy.",
      primaryButton = "Keep selected variant",
      secondaryButton = "Back to item",
    )
    setPanelHeader("Available finishes", "A variant choice now creates another actionable decision point.")
    showRadioPanel(
      optionOne = "Graphite - best seller",
      optionTwo = "Sand - lighter fabric",
      optionThree = "Forest - water-resistant shell",
      selectedValue = selectedColor,
    )
    showCheckboxPanel(
      optionOne = "Show customer photos" to true,
      optionTwo = "4 stars and up only" to true,
      optionThree = "Only in-stock finishes" to true,
      optionFour = "Highlight fastest delivery" to false,
    )
    setActionButtons(
      primaryLabel = "Keep selected variant",
      onPrimary = {
        selectedColor = currentRadioSelection()
        if (selectedColor.isBlank()) {
          showStatus("Pick a variant before returning to the cart flow.")
        } else {
          navigateTo(SCREEN_SHOPPING_CART)
        }
      },
      secondaryLabel = "Back to item",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderShoppingCart() {
    bindCommon(
      appName = "Amazon Shopping",
      pathLabel = "Cart / Travel gear",
      stepLabel = "Step 4 of 5",
      title = "Cart review",
      subtitle = "The detour now reaches a cart page before checkout instead of stopping on the product page.",
      body =
        "Item: ${selectedDeal.ifBlank { "Travel gear item" }}\n" +
          "Variant: ${selectedColor.ifBlank { "Default" }}\n" +
          "Shipping: ${selectedShipping.ifBlank { "Not selected" }}",
      primaryButton = "Proceed to checkout",
      secondaryButton = "Back to deals",
    )
    setPanelHeader("Fulfillment choice", "Pick how the item should be delivered before opening checkout.")
    showRadioPanel(
      optionOne = "Home delivery",
      optionTwo = "Locker pickup",
      optionThree = "Weekend drop-off",
      selectedValue = selectedFulfillment,
    )
    showCheckboxPanel(
      optionOne = "Ship in fewer boxes" to false,
      optionTwo = "Use saved coupon if available" to applyCoupon,
      optionThree = "Carbon-neutral delivery" to false,
      optionFour = "Keep item in cart after session" to false,
    )
    setActionButtons(
      primaryLabel = "Proceed to checkout",
      onPrimary = {
        selectedFulfillment = currentRadioSelection()
        if (selectedFulfillment.isBlank()) {
          showStatus("Choose a fulfillment method before checkout.")
        } else {
          navigateTo(SCREEN_SHOPPING_CHECKOUT)
        }
      },
      secondaryLabel = "Back to deals",
      onSecondary = { restartFlowAt(SCREEN_SHOPPING_AMAZON) },
    )
  }

  private fun renderShoppingCheckout() {
    bindCommon(
      appName = "Amazon Shopping",
      pathLabel = "Checkout / Payment",
      stepLabel = "Step 5 of 5",
      title = "Checkout",
      subtitle = "The flash-sale flow now ends only after cart and payment decisions.",
      body =
        "Order summary\n\n" +
          "• ${selectedDeal.ifBlank { "Travel gear item" }}\n" +
          "• Fulfillment: ${selectedFulfillment.ifBlank { "Not selected" }}\n" +
          "• Variant: ${selectedColor.ifBlank { "Default" }}",
      primaryButton = "Place order",
      secondaryButton = "Review cart",
    )
    setPanelHeader("Payment method", "A final decision is now required before the flow can finish.")
    showRadioPanel(
      optionOne = "Visa ending in 2048",
      optionTwo = "Gift card balance",
      optionThree = "PayPal",
      selectedValue = selectedPaymentMethod,
    )
    showCheckboxPanel(
      optionOne = "Email me a receipt" to true,
      optionTwo = "Save this payment choice" to true,
      optionThree = "Use one-click checkout next time" to false,
      optionFour = "" to false,
    )
    setActionButtons(
      primaryLabel = "Place order",
      onPrimary = {
        selectedPaymentMethod = currentRadioSelection()
        if (selectedPaymentMethod.isBlank()) {
          showStatus("Choose a payment method before finishing checkout.")
        } else {
          navigateTo(SCREEN_SHOPPING_CONFIRMATION)
        }
      },
      secondaryLabel = "Review cart",
      onSecondary = { goBackOne() },
    )
  }

  private fun renderShoppingConfirmation() {
    bindCommon(
      appName = "Amazon Shopping",
      pathLabel = "Checkout / Confirmation",
      stepLabel = "Placed",
      title = "Order ready to place",
      subtitle = "The flash-sale perturbation now spans a full shopping path.",
      body =
        "Item: ${selectedDeal.ifBlank { "Travel gear item" }}\n" +
          "Shipping: ${selectedShipping.ifBlank { "Not selected" }}\n" +
          "Fulfillment: ${selectedFulfillment.ifBlank { "Not selected" }}\n" +
          "Payment: ${selectedPaymentMethod.ifBlank { "Not selected" }}",
      primaryButton = "Done",
      secondaryButton = "Start over",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
      secondaryLabel = "Start over",
      onSecondary = { restartFlowAt(SCREEN_SHOPPING_AMAZON) },
    )
  }

  private fun renderGenericFallback() {
    bindCommon(
      appName = "Interruption Details",
      pathLabel = "Helper destination",
      stepLabel = "Follow-up",
      title = "Follow-up destination",
      subtitle = "This screen exists to prevent the perturbation from ending after one tap.",
      body = "This destination does not yet have a custom multi-step flow.",
      primaryButton = "Done",
      secondaryButton = "",
    )
    setActionButtons(
      primaryLabel = "Done",
      onPrimary = { finish() },
    )
  }

  private fun bindCommon(
    appName: String,
    pathLabel: String,
    stepLabel: String,
    title: String,
    subtitle: String,
    body: String,
    primaryButton: String,
    secondaryButton: String,
  ) {
    binding.destinationAppName.text = appName
    binding.destinationPath.text = pathLabel
    binding.destinationStepLabel.text = stepLabel
    binding.destinationTitle.text = title
    binding.destinationSubtitle.text = subtitle
    binding.destinationBody.text = body
    binding.destinationPrimaryButton.text = primaryButton
    binding.destinationSecondaryButton.text = secondaryButton
    binding.destinationSecondaryButton.visibility =
      if (secondaryButton.isBlank()) View.GONE else View.VISIBLE
  }

  private fun resetForm() {
    binding.destinationFormCard.visibility = View.GONE
    binding.destinationPanelTitle.visibility = View.GONE
    binding.destinationPanelSubtitle.visibility = View.GONE
    binding.destinationSwitchPanel.visibility = View.GONE
    binding.destinationCheckboxPanel.visibility = View.GONE
    binding.destinationRadioPanel.visibility = View.GONE
    binding.destinationQuickActionPanel.visibility = View.GONE
    binding.destinationRatingPanel.visibility = View.GONE
    binding.destinationInputPanel.visibility = View.GONE
    binding.destinationMapPanel.visibility = View.GONE
    binding.destinationProgressPanel.visibility = View.GONE
    binding.destinationSummaryFooter.visibility = View.GONE
  }

  private fun setPanelHeader(title: String, subtitle: String = "") {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationPanelTitle.visibility = View.VISIBLE
    binding.destinationPanelTitle.text = title
    binding.destinationPanelSubtitle.visibility =
      if (subtitle.isBlank()) View.GONE else View.VISIBLE
    binding.destinationPanelSubtitle.text = subtitle
  }

  private fun showSwitchPanel(
    optionOne: Pair<String, Boolean>,
    optionTwo: Pair<String, Boolean>,
    optionThree: Pair<String, Boolean>,
  ) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationSwitchPanel.visibility = View.VISIBLE
    bindSwitch(binding.destinationSwitchOne, optionOne.first, optionOne.second)
    bindSwitch(binding.destinationSwitchTwo, optionTwo.first, optionTwo.second)
    bindSwitch(binding.destinationSwitchThree, optionThree.first, optionThree.second)
  }

  private fun showCheckboxPanel(
    optionOne: Pair<String, Boolean>,
    optionTwo: Pair<String, Boolean>,
    optionThree: Pair<String, Boolean>,
    optionFour: Pair<String, Boolean>,
  ) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationCheckboxPanel.visibility = View.VISIBLE
    bindCheckbox(binding.destinationCheckboxOne, optionOne.first, optionOne.second)
    bindCheckbox(binding.destinationCheckboxTwo, optionTwo.first, optionTwo.second)
    bindCheckbox(binding.destinationCheckboxThree, optionThree.first, optionThree.second)
    bindCheckbox(binding.destinationCheckboxFour, optionFour.first, optionFour.second)
  }

  private fun showRadioPanel(
    optionOne: String,
    optionTwo: String,
    optionThree: String,
    selectedValue: String,
  ) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationRadioPanel.visibility = View.VISIBLE
    bindRadio(binding.destinationRadioOne, optionOne)
    bindRadio(binding.destinationRadioTwo, optionTwo)
    bindRadio(binding.destinationRadioThree, optionThree)
    binding.destinationRadioGroup.clearCheck()
    when (selectedValue) {
      optionOne -> binding.destinationRadioOne.isChecked = true
      optionTwo -> binding.destinationRadioTwo.isChecked = true
      optionThree -> binding.destinationRadioThree.isChecked = true
    }
  }

  private fun showQuickActions(
    firstLabel: String = "",
    onFirst: () -> Unit = {},
    secondLabel: String = "",
    onSecond: () -> Unit = {},
    thirdLabel: String = "",
    onThird: () -> Unit = {},
  ) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationQuickActionPanel.visibility = View.VISIBLE
    bindQuickAction(binding.destinationQuickActionOne, firstLabel, onFirst)
    bindQuickAction(binding.destinationQuickActionTwo, secondLabel, onSecond)
    bindQuickAction(binding.destinationQuickActionThree, thirdLabel, onThird)
  }

  private fun showRatingPanel(value: Float) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationRatingPanel.visibility = View.VISIBLE
    binding.destinationRatingBar.rating = value
  }

  private fun showInputPanel(hint: String, value: String) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationInputPanel.visibility = View.VISIBLE
    binding.destinationInput.hint = hint
    binding.destinationInput.setText(value)
    binding.destinationInput.setSelection(binding.destinationInput.text?.length ?: 0)
  }

  private fun showMapPanel(canvasLabel: String, metaLabel: String) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationMapPanel.visibility = View.VISIBLE
    binding.destinationMapCanvas.text = canvasLabel
    binding.destinationMapMeta.text = metaLabel
  }

  private fun showProgressPanel(progress: Int, caption: String) {
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationProgressPanel.visibility = View.VISIBLE
    binding.destinationProgressBar.progress = progress
    binding.destinationProgressCaption.text = caption
  }

  private fun setSummaryFooter(text: String) {
    if (text.isBlank()) {
      binding.destinationSummaryFooter.visibility = View.GONE
      return
    }
    binding.destinationFormCard.visibility = View.VISIBLE
    binding.destinationSummaryFooter.visibility = View.VISIBLE
    binding.destinationSummaryFooter.text = text
  }

  private fun setActionButtons(
    primaryLabel: String,
    onPrimary: () -> Unit,
    secondaryLabel: String = "",
    onSecondary: () -> Unit = {},
  ) {
    binding.destinationPrimaryButton.text = primaryLabel
    binding.destinationPrimaryButton.setOnClickListener { onPrimary() }
    if (secondaryLabel.isBlank()) {
      binding.destinationSecondaryButton.visibility = View.GONE
      binding.destinationSecondaryButton.setOnClickListener(null)
    } else {
      binding.destinationSecondaryButton.visibility = View.VISIBLE
      binding.destinationSecondaryButton.text = secondaryLabel
      binding.destinationSecondaryButton.setOnClickListener { onSecondary() }
    }
  }

  private fun bindSwitch(view: View, label: String, checked: Boolean) {
    val switchView = view as com.google.android.material.switchmaterial.SwitchMaterial
    switchView.visibility = if (label.isBlank()) View.GONE else View.VISIBLE
    if (label.isNotBlank()) {
      switchView.text = label
      switchView.isChecked = checked
    }
  }

  private fun bindCheckbox(view: View, label: String, checked: Boolean) {
    val checkbox = view as android.widget.CheckBox
    checkbox.visibility = if (label.isBlank()) View.GONE else View.VISIBLE
    if (label.isNotBlank()) {
      checkbox.text = label
      checkbox.isChecked = checked
    }
  }

  private fun bindRadio(view: View, label: String) {
    val radio = view as android.widget.RadioButton
    radio.visibility = if (label.isBlank()) View.GONE else View.VISIBLE
    if (label.isNotBlank()) {
      radio.text = label
    }
  }

  private fun bindQuickAction(view: View, label: String, onClick: () -> Unit) {
    val button = view as android.widget.Button
    button.visibility = if (label.isBlank()) View.GONE else View.VISIBLE
    if (label.isNotBlank()) {
      button.text = label
      button.setOnClickListener { onClick() }
    } else {
      button.setOnClickListener(null)
    }
  }

  private fun showStatus(message: String) {
    binding.destinationStatus.visibility = View.VISIBLE
    binding.destinationStatus.text = message
  }

  private fun clearStatus() {
    binding.destinationStatus.visibility = View.GONE
    binding.destinationStatus.text = ""
  }

  private fun navigateTo(screenId: String) {
    backStack.add(screenId)
    renderCurrentScreen()
  }

  private fun restartFlowAt(screenId: String) {
    backStack.clear()
    backStack.add(screenId)
    renderCurrentScreen()
  }

  private fun goBackOne() {
    if (backStack.size <= 1) {
      finish()
      return
    }
    backStack.removeAt(backStack.lastIndex)
    renderCurrentScreen()
  }

  private fun currentRadioSelection(): String {
    return when (binding.destinationRadioGroup.checkedRadioButtonId) {
      R.id.destinationRadioOne -> binding.destinationRadioOne.text.toString()
      R.id.destinationRadioTwo -> binding.destinationRadioTwo.text.toString()
      R.id.destinationRadioThree -> binding.destinationRadioThree.text.toString()
      else -> ""
    }
  }

  private fun captureNotificationSwitches() {
    notificationsEnabled = binding.destinationSwitchOne.isChecked
    notificationPopOnScreen = binding.destinationSwitchTwo.isChecked
    notificationLockScreen = binding.destinationSwitchThree.isChecked
  }

  private fun captureNotificationCategories() {
    categoryDirectMessages = binding.destinationSwitchOne.isChecked
    categoryMentions = binding.destinationSwitchTwo.isChecked
    categoryReminders = binding.destinationSwitchThree.isChecked
  }

  private fun capturePrivacyPurposes() {
    privacyAnalytics = binding.destinationCheckboxOne.isChecked
    privacyPersonalized = binding.destinationCheckboxTwo.isChecked
    privacyMarketing = binding.destinationCheckboxThree.isChecked
    privacyLocation = binding.destinationCheckboxFour.isChecked
  }

  private fun capturePrivacyVendors() {
    vendorNewsDaily = binding.destinationCheckboxOne.isChecked
    vendorAudienceLab = binding.destinationCheckboxTwo.isChecked
    vendorAdExchange = binding.destinationCheckboxThree.isChecked
    vendorMeasurementStudio = binding.destinationCheckboxFour.isChecked
  }

  private fun captureRatingValue() {
    ratingStars = binding.destinationRatingBar.rating
  }

  private fun captureReviewDetails() {
    ratingStars = binding.destinationRatingBar.rating
    reasonEaseOfUse = binding.destinationCheckboxOne.isChecked
    reasonUseful = binding.destinationCheckboxTwo.isChecked
    reasonDesign = binding.destinationCheckboxThree.isChecked
    reasonBugs = binding.destinationCheckboxFour.isChecked
    reviewDraft = binding.destinationInput.text?.toString()?.trim().orEmpty()
  }

  private fun captureShoppingFeed() {
    selectedDeal = currentRadioSelection()
    filterPrimeOnly = binding.destinationCheckboxOne.isChecked
    filterUnderFifty = binding.destinationCheckboxTwo.isChecked
    filterCarryOn = binding.destinationCheckboxThree.isChecked
    filterFreeReturns = binding.destinationCheckboxFour.isChecked
  }

  private fun captureShoppingDetail() {
    selectedShipping = currentRadioSelection()
    addProtectionPlan = binding.destinationCheckboxOne.isChecked
    saveWishlist = binding.destinationCheckboxTwo.isChecked
    applyCoupon = binding.destinationCheckboxThree.isChecked
    giftWrap = binding.destinationCheckboxFour.isChecked
  }

  private fun captureMessageReply() {
    includeAttachmentInReply = binding.destinationCheckboxOne.isChecked
    mentionEta = binding.destinationCheckboxTwo.isChecked
    askForParking = binding.destinationCheckboxThree.isChecked
    replyDraft = binding.destinationInput.text?.toString()?.trim().orEmpty()
  }

  private fun captureDeliveryMapOptions() {
    shareLiveLocation = binding.destinationCheckboxOne.isChecked
    ringBell = binding.destinationCheckboxTwo.isChecked
    leavePhotoProof = binding.destinationCheckboxThree.isChecked
    avoidStairs = binding.destinationCheckboxFour.isChecked
  }

  private fun captureDeliverySafePlace() {
    selectedSafePlace = currentRadioSelection()
    deliveryNote = binding.destinationInput.text?.toString()?.trim().orEmpty()
  }

  private fun captureUpdatePlan() {
    installPlan = currentRadioSelection()
    backupBeforeRestart = binding.destinationCheckboxOne.isChecked
    updateWifiOnly = binding.destinationCheckboxTwo.isChecked
    pauseBatterySaver = binding.destinationCheckboxThree.isChecked
    backgroundRestart = binding.destinationCheckboxFour.isChecked
  }

  private fun captureDownloadOptions() {
    updateWifiOnly = binding.destinationCheckboxOne.isChecked
    remindBeforeRestart = binding.destinationCheckboxThree.isChecked
  }

  private fun captureRestartOptions() {
    restartWindow = currentRadioSelection()
    remindBeforeRestart = binding.destinationCheckboxOne.isChecked
    closeBackgroundApps = binding.destinationCheckboxTwo.isChecked
  }

  private fun captureAppStorePreferences() {
    autoUpdateOnWifi = binding.destinationCheckboxOne.isChecked
    openWhenDone = binding.destinationCheckboxTwo.isChecked
    notifyCompletion = binding.destinationCheckboxThree.isChecked
    downloadBetaAssets = binding.destinationCheckboxFour.isChecked
  }

  private fun captureAppStorePermissions() {
    changedPermissionLocation = binding.destinationCheckboxOne.isChecked
    changedPermissionNearby = binding.destinationCheckboxTwo.isChecked
    changedPermissionNotifications = binding.destinationCheckboxThree.isChecked
    changedPermissionCrashLogs = binding.destinationCheckboxFour.isChecked
  }

  private fun captureSecurityChecklist() {
    reviewedRequesterIdentity = binding.destinationCheckboxOne.isChecked
    understandProtectedSetting = binding.destinationCheckboxTwo.isChecked
    allowOnceOnly = binding.destinationCheckboxThree.isChecked
    rememberDecision = binding.destinationCheckboxFour.isChecked
  }

  private fun applyReplyTemplate(text: String) {
    replyDraft = text
    binding.destinationInput.setText(text)
    binding.destinationInput.setSelection(binding.destinationInput.text?.length ?: 0)
    showStatus("Quick reply inserted into the draft.")
  }

  private fun applyDriverTemplate(text: String) {
    driverMessage = text
    binding.destinationInput.setText(text)
    binding.destinationInput.setSelection(binding.destinationInput.text?.length ?: 0)
    showStatus("Driver note inserted into the message field.")
  }

  private fun applyReviewTemplate(text: String) {
    reviewDraft = text
    binding.destinationInput.setText(text)
    binding.destinationInput.setSelection(binding.destinationInput.text?.length ?: 0)
    showStatus("Suggested review text inserted. You can still edit it before submitting.")
  }

  private fun enabledNotificationCategories(): String {
    val items = mutableListOf<String>()
    if (categoryDirectMessages) items += "• Direct messages"
    if (categoryMentions) items += "• Mentions and reactions"
    if (categoryReminders) items += "• System reminders"
    return items.joinToString("\n")
  }

  private fun enabledPurposesSummary(): String {
    val items = mutableListOf<String>()
    if (privacyAnalytics) items += "• Analytics cookies"
    if (privacyPersonalized) items += "• Personalized content"
    if (privacyMarketing) items += "• Marketing identifiers"
    if (privacyLocation) items += "• Precise location personalization"
    return items.joinToString("\n").ifBlank { "• None" }
  }

  private fun enabledVendorsSummary(): String {
    val items = mutableListOf<String>()
    if (vendorNewsDaily) items += "• News Daily"
    if (vendorAudienceLab) items += "• Audience Lab"
    if (vendorAdExchange) items += "• Ad Exchange"
    if (vendorMeasurementStudio) items += "• Measurement Studio"
    return items.joinToString("\n").ifBlank { "• None" }
  }

  private fun enabledReviewReasons(): String {
    val items = mutableListOf<String>()
    if (reasonEaseOfUse) items += "Easy to use"
    if (reasonUseful) items += "Helpful features"
    if (reasonDesign) items += "Clean design"
    if (reasonBugs) items += "Needs bug fixes"
    return items.joinToString(", ").ifBlank { "No tags selected" }
  }

  private fun yesNo(value: Boolean): String = if (value) "Yes" else "No"

  companion object {
    private const val EXTRA_TEMPLATE = "destination_template"

    private const val SCREEN_GENERIC = "generic"
    private const val SCREEN_NOTIFICATION_SETTINGS = "notification_settings"
    private const val SCREEN_NOTIFICATION_CATEGORIES = "notification_categories"
    private const val SCREEN_NOTIFICATION_CONFIRMATION = "notification_confirmation"
    private const val SCREEN_SYSTEM_UPDATE_SETTINGS = "system_update_settings"
    private const val SCREEN_SYSTEM_UPDATE_CHANGELOG = "system_update_changelog"
    private const val SCREEN_SYSTEM_UPDATE_DOWNLOAD = "system_update_download"
    private const val SCREEN_SYSTEM_UPDATE_RESTART = "system_update_restart"
    private const val SCREEN_SYSTEM_UPDATE_CONFIRMED = "system_update_confirmed"
    private const val SCREEN_APP_STORE_UPDATE = "app_store_update"
    private const val SCREEN_APP_STORE_PERMISSIONS = "app_store_permissions"
    private const val SCREEN_APP_STORE_QUEUE = "app_store_queue"
    private const val SCREEN_MESSAGE_THREAD = "message_thread"
    private const val SCREEN_MESSAGE_REPLY = "message_reply"
    private const val SCREEN_MESSAGE_ATTACHMENT = "message_attachment"
    private const val SCREEN_MESSAGE_SENT = "message_sent"
    private const val SCREEN_DELIVERY_TRACKING = "delivery_tracking"
    private const val SCREEN_DELIVERY_MAP = "delivery_map"
    private const val SCREEN_DELIVERY_SAFE_PLACE = "delivery_safe_place"
    private const val SCREEN_DELIVERY_CONTACT = "delivery_contact"
    private const val SCREEN_DELIVERY_CONFIRMATION = "delivery_confirmation"
    private const val SCREEN_PRIVACY_OPTIONS = "privacy_options"
    private const val SCREEN_PRIVACY_VENDORS = "privacy_vendors"
    private const val SCREEN_PRIVACY_SUMMARY = "privacy_summary"
    private const val SCREEN_SECURITY_CENTER = "security_center"
    private const val SCREEN_SECURITY_REVIEW = "security_review"
    private const val SCREEN_SECURITY_CONFIRMED = "security_confirmed"
    private const val SCREEN_RATING_FLOW = "rating_flow"
    private const val SCREEN_RATING_REVIEW = "rating_review"
    private const val SCREEN_RATING_CONFIRMATION = "rating_confirmation"
    private const val SCREEN_SHOPPING_AMAZON = "shopping_amazon"
    private const val SCREEN_SHOPPING_DETAIL = "shopping_detail"
    private const val SCREEN_SHOPPING_COMPARE = "shopping_compare"
    private const val SCREEN_SHOPPING_CART = "shopping_cart"
    private const val SCREEN_SHOPPING_CHECKOUT = "shopping_checkout"
    private const val SCREEN_SHOPPING_CONFIRMATION = "shopping_confirmation"

    fun newIntent(context: Context, template: String): Intent {
      return Intent(context, DestinationActivity::class.java).apply {
        putExtra(EXTRA_TEMPLATE, template)
      }
    }

    private fun initialScreenFor(template: String): String {
      return when (template) {
        SCREEN_NOTIFICATION_SETTINGS,
        SCREEN_SYSTEM_UPDATE_SETTINGS,
        SCREEN_APP_STORE_UPDATE,
        SCREEN_MESSAGE_THREAD,
        SCREEN_DELIVERY_TRACKING,
        SCREEN_PRIVACY_OPTIONS,
        SCREEN_SECURITY_CENTER,
        SCREEN_RATING_FLOW,
        SCREEN_SHOPPING_AMAZON -> template
        else -> SCREEN_GENERIC
      }
    }
  }
}
