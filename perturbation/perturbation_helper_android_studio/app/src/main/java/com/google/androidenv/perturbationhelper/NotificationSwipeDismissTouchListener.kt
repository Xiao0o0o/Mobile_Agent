package com.google.androidenv.perturbationhelper

import android.view.MotionEvent
import android.view.View
import kotlin.math.abs

class NotificationSwipeDismissTouchListener(
  private val target: View,
  private val onDismissed: () -> Unit,
) : View.OnTouchListener {

  private var downX = 0f
  private var dragging = false

  override fun onTouch(view: View, event: MotionEvent): Boolean {
    when (event.actionMasked) {
      MotionEvent.ACTION_DOWN -> {
        downX = event.rawX
        dragging = false
      }
      MotionEvent.ACTION_MOVE -> {
        val deltaX = event.rawX - downX
        if (abs(deltaX) > 12f) {
          dragging = true
          target.translationX = deltaX
          target.alpha = (1f - (abs(deltaX) / target.width.toFloat()).coerceAtMost(0.65f))
        }
      }
      MotionEvent.ACTION_UP,
      MotionEvent.ACTION_CANCEL -> {
        val deltaX = event.rawX - downX
        if (dragging && abs(deltaX) > target.width * 0.3f) {
          val destination = if (deltaX > 0) target.width.toFloat() else -target.width.toFloat()
          target.animate()
            .translationX(destination)
            .alpha(0f)
            .setDuration(150L)
            .withEndAction { onDismissed() }
            .start()
          return true
        }
        target.animate()
          .translationX(0f)
          .alpha(1f)
          .setDuration(150L)
          .start()
      }
    }
    return dragging
  }
}
