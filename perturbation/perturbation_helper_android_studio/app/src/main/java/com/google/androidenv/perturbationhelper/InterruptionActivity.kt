package com.google.androidenv.perturbationhelper

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.FrameLayout
import android.view.Gravity
import android.view.View
import android.widget.LinearLayout
import androidx.activity.addCallback
import androidx.appcompat.app.AppCompatActivity
import com.google.androidenv.perturbationhelper.databinding.ActivityInterruptionBinding
import kotlin.math.roundToInt

class InterruptionActivity : AppCompatActivity() {

  private lateinit var binding: ActivityInterruptionBinding
  private val handler = Handler(Looper.getMainLooper())
  private var autoDismissRunnable: Runnable? = null
  private lateinit var spec: InterruptionSpec

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    binding = ActivityInterruptionBinding.inflate(layoutInflater)
    setContentView(binding.root)

    onBackPressedDispatcher.addCallback(this) {
      emitResult(InterruptionContract.RESULT_BACK)
      finish()
    }

    spec = InterruptionSpec.fromIntent(intent)
    renderSpec(spec)
  }

  override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    setIntent(intent)
    spec = InterruptionSpec.fromIntent(intent)
    renderSpec(spec)
  }

  override fun onDestroy() {
    autoDismissRunnable?.let { handler.removeCallbacks(it) }
    super.onDestroy()
  }

  private fun renderSpec(spec: InterruptionSpec) {
    autoDismissRunnable?.let { handler.removeCallbacks(it) }

    binding.scrim.setOnClickListener {
      if (!spec.blocking) {
        emitResult(InterruptionContract.RESULT_BACKGROUND)
        finish()
      }
    }
    setFinishOnTouchOutside(!spec.blocking && spec.surfaceStyle != InterruptionSurfaceStyle.BANNER)

    when (spec.surfaceStyle) {
      InterruptionSurfaceStyle.BANNER -> showNotification(spec)
      InterruptionSurfaceStyle.BOTTOM_SHEET -> showBottomSheet(spec)
      InterruptionSurfaceStyle.INTERSTITIAL -> showInterstitial(spec)
      InterruptionSurfaceStyle.DIALOG -> showDialog(spec)
    }

    if (spec.autoDismissMs > 0L) {
      autoDismissRunnable = Runnable {
        emitResult(InterruptionContract.RESULT_TIMEOUT)
        finish()
      }
      handler.postDelayed(autoDismissRunnable!!, spec.autoDismissMs)
    }
  }

  private fun showDialog(spec: InterruptionSpec) {
    applyDialogSurfaceLayout(
      gravity = Gravity.CENTER,
      topMarginDp = 24,
      bottomMarginDp = 24,
      horizontalMarginDp = 24,
      accentWidthDp = 64,
      accentHeightDp = 8,
      buttonRowOrientation = LinearLayout.HORIZONTAL,
      stackedButtons = false,
      minHeightFraction = 0f,
    )
    binding.dialogCardRoot.visibility = android.view.View.VISIBLE
    binding.notificationBannerCard.visibility = android.view.View.GONE
    binding.scrim.visibility = android.view.View.VISIBLE

    binding.dialogBadge.text = spec.type.badge
    binding.dialogAppName.text = spec.appName
    binding.dialogTitle.text = spec.title
    binding.dialogMessage.text = spec.message
    binding.dialogPrimaryButton.text = spec.primaryButton
    binding.dialogSecondaryButton.text = spec.secondaryButton
    binding.dialogAccent.setBackgroundColor(accentColor(spec.type))
    binding.dialogPrimaryButton.setBackgroundColor(accentColor(spec.type))
    binding.dialogPrimaryButton.setTextColor(Color.WHITE)
    binding.dialogSecondaryButton.setTextColor(accentColor(spec.type))

    binding.dialogPrimaryButton.setOnClickListener {
      handleButton(isPrimary = true)
    }
    binding.dialogSecondaryButton.setOnClickListener {
      handleButton(isPrimary = false)
    }
  }

  private fun showBottomSheet(spec: InterruptionSpec) {
    applyDialogSurfaceLayout(
      gravity = Gravity.BOTTOM,
      topMarginDp = 108,
      bottomMarginDp = 0,
      horizontalMarginDp = 0,
      accentWidthDp = 72,
      accentHeightDp = 10,
      buttonRowOrientation = LinearLayout.VERTICAL,
      stackedButtons = true,
      minHeightFraction = 0.46f,
    )
    binding.dialogCardRoot.visibility = View.VISIBLE
    binding.notificationBannerCard.visibility = View.GONE
    binding.scrim.visibility = View.VISIBLE

    binding.dialogBadge.text = spec.type.badge
    binding.dialogAppName.text = spec.appName
    binding.dialogTitle.text = spec.title
    binding.dialogMessage.text = spec.message
    binding.dialogPrimaryButton.text = spec.primaryButton
    binding.dialogSecondaryButton.text = spec.secondaryButton
    binding.dialogAccent.setBackgroundColor(accentColor(spec.type))
    binding.dialogPrimaryButton.setBackgroundColor(accentColor(spec.type))
    binding.dialogPrimaryButton.setTextColor(Color.WHITE)
    binding.dialogSecondaryButton.setTextColor(accentColor(spec.type))

    binding.dialogPrimaryButton.setOnClickListener {
      handleButton(isPrimary = true)
    }
    binding.dialogSecondaryButton.setOnClickListener {
      handleButton(isPrimary = false)
    }
  }

  private fun showInterstitial(spec: InterruptionSpec) {
    applyDialogSurfaceLayout(
      gravity = Gravity.CENTER,
      topMarginDp = 12,
      bottomMarginDp = 12,
      horizontalMarginDp = 12,
      accentWidthDp = 0,
      accentHeightDp = 64,
      buttonRowOrientation = LinearLayout.VERTICAL,
      stackedButtons = true,
      fullWidthAccent = true,
      minHeightFraction = 0f,
    )
    binding.dialogCardRoot.visibility = View.VISIBLE
    binding.notificationBannerCard.visibility = View.GONE
    binding.scrim.visibility = View.VISIBLE

    binding.dialogBadge.text = spec.type.badge
    binding.dialogAppName.text = spec.appName
    binding.dialogTitle.text = spec.title
    binding.dialogMessage.text = spec.message
    binding.dialogPrimaryButton.text = spec.primaryButton
    binding.dialogSecondaryButton.text = spec.secondaryButton
    binding.dialogAccent.setBackgroundColor(accentColor(spec.type))
    binding.dialogPrimaryButton.setBackgroundColor(accentColor(spec.type))
    binding.dialogPrimaryButton.setTextColor(Color.WHITE)
    binding.dialogSecondaryButton.setTextColor(accentColor(spec.type))

    binding.dialogPrimaryButton.setOnClickListener {
      handleButton(isPrimary = true)
    }
    binding.dialogSecondaryButton.setOnClickListener {
      handleButton(isPrimary = false)
    }
  }

  private fun showNotification(spec: InterruptionSpec) {
    binding.dialogCardRoot.visibility = android.view.View.GONE
    binding.notificationBannerCard.visibility = android.view.View.VISIBLE
    binding.scrim.visibility = android.view.View.GONE

    binding.bannerAccent.setBackgroundColor(accentColor(spec.type))
    binding.bannerAppName.text = spec.appName
    binding.bannerTitle.text = spec.title
    binding.bannerMessage.text = spec.message
    binding.bannerPrimaryButton.text = spec.primaryButton
    binding.bannerSecondaryButton.text = spec.secondaryButton
    binding.bannerPrimaryButton.setOnClickListener {
      handleButton(isPrimary = true)
    }
    binding.bannerSecondaryButton.setOnClickListener {
      handleButton(isPrimary = false)
    }
    binding.notificationBannerCard.setOnTouchListener(
      NotificationSwipeDismissTouchListener(binding.notificationBannerCard) {
        emitResult(InterruptionContract.RESULT_SWIPE)
        finish()
      }
    )
  }

  private fun emitResult(result: String) {
    sendBroadcast(
      Intent(InterruptionContract.ACTION_INTERRUPTION_RESULT).apply {
        setPackage(packageName)
        putExtra(InterruptionContract.EXTRA_RESULT, result)
        putExtra(InterruptionContract.EXTRA_KIND, spec.type.wireValue)
        putExtra(InterruptionContract.EXTRA_SURFACE_STYLE, spec.surfaceStyle.wireValue)
        putExtra(InterruptionContract.EXTRA_INSTANCE_ID, spec.instanceId)
        putExtra(InterruptionContract.EXTRA_TIMESTAMP, System.currentTimeMillis())
      }
    )
  }

  private fun handleButton(isPrimary: Boolean) {
    val result =
      if (isPrimary) InterruptionContract.RESULT_PRIMARY else InterruptionContract.RESULT_SECONDARY
    val action = if (isPrimary) spec.primaryAction else spec.secondaryAction
    val destination = if (isPrimary) spec.primaryDestination else spec.secondaryDestination
    emitResult(result)
    if (action == "open_destination") {
      openDestination(destination)
    }
    finish()
  }

  private fun openDestination(destination: String) {
    if (destination.isBlank()) return
    startActivity(DestinationActivity.newIntent(this, destination))
  }

  private fun accentColor(type: InterruptionType): Int {
    val colorRes = when (type) {
      InterruptionType.POPUP -> R.color.popup_accent
      InterruptionType.AD -> R.color.ad_accent
      InterruptionType.UPDATE -> R.color.update_accent
      InterruptionType.NOTIFICATION -> R.color.notification_accent
    }
    return resources.getColor(colorRes, theme)
  }

  private fun applyDialogSurfaceLayout(
    gravity: Int,
    topMarginDp: Int,
    bottomMarginDp: Int,
    horizontalMarginDp: Int,
    accentWidthDp: Int,
    accentHeightDp: Int,
    buttonRowOrientation: Int,
    stackedButtons: Boolean,
    fullWidthAccent: Boolean = false,
    minHeightFraction: Float = 0f,
  ) {
    val cardParams = binding.dialogCardRoot.layoutParams as FrameLayout.LayoutParams
    cardParams.width = FrameLayout.LayoutParams.MATCH_PARENT
    cardParams.height =
      if (minHeightFraction > 0f) {
        (resources.displayMetrics.heightPixels * minHeightFraction).roundToInt()
      } else {
        FrameLayout.LayoutParams.WRAP_CONTENT
      }
    cardParams.gravity = gravity
    cardParams.marginStart = dp(horizontalMarginDp)
    cardParams.topMargin = dp(topMarginDp)
    cardParams.marginEnd = dp(horizontalMarginDp)
    cardParams.bottomMargin = dp(bottomMarginDp)
    binding.dialogCardRoot.layoutParams = cardParams
    binding.dialogCardRoot.radius = if (gravity == Gravity.BOTTOM) dp(30).toFloat() else dp(32).toFloat()
    binding.dialogCardRoot.minimumHeight =
      if (minHeightFraction > 0f) {
        (resources.displayMetrics.heightPixels * minHeightFraction).roundToInt()
      } else {
        0
      }

    val accentParams = binding.dialogAccent.layoutParams as LinearLayout.LayoutParams
    accentParams.width =
      if (fullWidthAccent) LinearLayout.LayoutParams.MATCH_PARENT else dp(accentWidthDp)
    accentParams.height = dp(accentHeightDp)
    binding.dialogAccent.layoutParams = accentParams

    val contentPaddingHorizontal = if (gravity == Gravity.BOTTOM) 20 else 24
    val contentPaddingTop = if (gravity == Gravity.BOTTOM) 22 else 24
    val contentPaddingBottom = if (gravity == Gravity.BOTTOM) 20 else 24
    binding.dialogContentRoot.setPadding(
      dp(contentPaddingHorizontal),
      dp(contentPaddingTop),
      dp(contentPaddingHorizontal),
      dp(contentPaddingBottom),
    )

    val spacerParams = binding.dialogSpacer.layoutParams as LinearLayout.LayoutParams
    spacerParams.height = 0
    spacerParams.weight = if (minHeightFraction > 0f) 1f else 0f
    binding.dialogSpacer.layoutParams = spacerParams

    binding.dialogButtonRow.orientation = buttonRowOrientation
    updateButtonLayout(binding.dialogPrimaryButton, stackedButtons)
    updateButtonLayout(binding.dialogSecondaryButton, stackedButtons)
    binding.dialogButtonRow.gravity = if (stackedButtons) Gravity.BOTTOM else Gravity.END
    binding.dialogSecondaryButton.visibility =
      if (spec.secondaryButton.isBlank()) View.GONE else View.VISIBLE
    binding.dialogPrimaryButton.visibility =
      if (spec.primaryButton.isBlank()) View.GONE else View.VISIBLE
  }

  private fun updateButtonLayout(button: View, stacked: Boolean) {
    val params = button.layoutParams as LinearLayout.LayoutParams
    if (stacked) {
      params.width = LinearLayout.LayoutParams.MATCH_PARENT
      params.weight = 0f
      params.marginStart = 0
      if (button.id == R.id.dialogPrimaryButton) {
        params.topMargin = dp(10)
      } else {
        params.topMargin = 0
      }
    } else {
      params.width = LinearLayout.LayoutParams.WRAP_CONTENT
      params.weight = 0f
      params.topMargin = 0
      if (button.id == R.id.dialogPrimaryButton) {
        params.marginStart = dp(12)
      } else {
        params.marginStart = 0
      }
    }
    button.layoutParams = params
  }

  private fun dp(value: Int): Int {
    return (value * resources.displayMetrics.density).roundToInt()
  }
}
