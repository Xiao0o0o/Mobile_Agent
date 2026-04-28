package com.google.androidenv.perturbationhelper

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.widget.ArrayAdapter
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.card.MaterialCardView
import com.google.android.material.snackbar.Snackbar
import com.google.androidenv.perturbationhelper.databinding.ActivityMainBinding
import com.google.androidenv.perturbationhelper.databinding.ItemPresetBinding

class MainActivity : AppCompatActivity() {

  private lateinit var binding: ActivityMainBinding
  private val resultReceiver = object : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
      if (intent == null) return
      val result = intent.getStringExtra(InterruptionContract.EXTRA_RESULT).orEmpty()
      val kind = intent.getStringExtra(InterruptionContract.EXTRA_KIND).orEmpty()
      val surface = intent.getStringExtra(InterruptionContract.EXTRA_SURFACE_STYLE).orEmpty()
      val instanceId = intent.getStringExtra(InterruptionContract.EXTRA_INSTANCE_ID).orEmpty()
      binding.lastResultTitle.text = getString(R.string.last_result_title)
      binding.lastResultBody.text =
        "Type: $kind\nSurface: $surface\nAction: $result\nInstance: $instanceId"
    }
  }

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    binding = ActivityMainBinding.inflate(layoutInflater)
    setContentView(binding.root)

    setupTypeSpinner()
    setupSurfaceSpinner()
    renderPresetGallery()
    bindEditorActions()
    fillEditor(PresetRepository.defaultSpecFor(InterruptionType.POPUP))
  }

  override fun onStart() {
    super.onStart()
    val filter = IntentFilter(InterruptionContract.ACTION_INTERRUPTION_RESULT)
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
      registerReceiver(resultReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
    } else {
      @Suppress("DEPRECATION")
      registerReceiver(resultReceiver, filter)
    }
  }

  override fun onStop() {
    unregisterReceiver(resultReceiver)
    super.onStop()
  }

  private fun setupTypeSpinner() {
    val adapter = ArrayAdapter(
      this,
      android.R.layout.simple_spinner_dropdown_item,
      InterruptionType.entries.map { it.displayName },
    )
    binding.typeSpinner.adapter = adapter
    binding.typeSpinner.setSelection(InterruptionType.entries.indexOf(InterruptionType.POPUP))
  }

  private fun setupSurfaceSpinner() {
    val adapter = ArrayAdapter(
      this,
      android.R.layout.simple_spinner_dropdown_item,
      InterruptionSurfaceStyle.entries.map { it.displayName },
    )
    binding.surfaceStyleSpinner.adapter = adapter
    binding.surfaceStyleSpinner.setSelection(
      InterruptionSurfaceStyle.entries.indexOf(InterruptionSurfaceStyle.DIALOG)
    )
  }

  private fun renderPresetGallery() {
    val inflater = LayoutInflater.from(this)
    binding.presetContainer.removeAllViews()

    InterruptionType.entries.forEach { type ->
      val header = inflater.inflate(
        R.layout.item_section_header,
        binding.presetContainer,
        false,
      ) as TextView
      header.text = type.displayName
      binding.presetContainer.addView(header)

      PresetRepository.presets
        .filter { it.type == type }
        .forEach { preset ->
          val itemBinding = ItemPresetBinding.inflate(inflater, binding.presetContainer, false)
          itemBinding.presetBadge.text = preset.type.badge
          itemBinding.presetTitle.text = preset.name
          itemBinding.presetSummary.text = preset.summary
          itemBinding.launchPresetButton.setOnClickListener {
            launchInterruption(preset.spec)
          }
          itemBinding.loadPresetButton.setOnClickListener {
            fillEditor(preset.spec)
            Snackbar.make(binding.root, "Loaded ${preset.name} into the editor.", Snackbar.LENGTH_SHORT).show()
          }

          val card = itemBinding.root as MaterialCardView
          card.setCardBackgroundColor(resources.getColor(R.color.surface_container, theme))
          binding.presetContainer.addView(card)
        }
    }
  }

  private fun bindEditorActions() {
    binding.loadDefaultsButton.setOnClickListener {
      val selectedType = currentSelectedType()
      fillEditor(PresetRepository.defaultSpecFor(selectedType))
    }
    binding.launchConfiguredButton.setOnClickListener {
      launchInterruption(collectSpecFromEditor())
    }
  }

  private fun currentSelectedType(): InterruptionType {
    return InterruptionType.entries[binding.typeSpinner.selectedItemPosition]
  }

  private fun fillEditor(spec: InterruptionSpec) {
    binding.typeSpinner.setSelection(InterruptionType.entries.indexOf(spec.type))
    binding.appNameInput.setText(spec.appName)
    binding.surfaceStyleSpinner.setSelection(
      InterruptionSurfaceStyle.entries.indexOf(spec.surfaceStyle)
    )
    binding.titleInput.setText(spec.title)
    binding.messageInput.setText(spec.message)
    binding.primaryButtonInput.setText(spec.primaryButton)
    binding.secondaryButtonInput.setText(spec.secondaryButton)
    binding.blockingSwitch.isChecked = spec.blocking
    binding.autoDismissInput.setText(
      if (spec.autoDismissMs > 0) spec.autoDismissMs.toString() else ""
    )
  }

  private fun collectSpecFromEditor(): InterruptionSpec {
    val autoDismissMs = binding.autoDismissInput.text?.toString()?.trim()?.toLongOrNull() ?: 0L
    return InterruptionSpec(
      type = currentSelectedType(),
      surfaceStyle = InterruptionSurfaceStyle.entries[binding.surfaceStyleSpinner.selectedItemPosition],
      appName = binding.appNameInput.text?.toString()?.trim().orEmpty(),
      title = binding.titleInput.text?.toString()?.trim().orEmpty(),
      message = binding.messageInput.text?.toString()?.trim().orEmpty(),
      primaryButton = binding.primaryButtonInput.text?.toString()?.trim().orEmpty(),
      secondaryButton = binding.secondaryButtonInput.text?.toString()?.trim().orEmpty(),
      blocking = binding.blockingSwitch.isChecked,
      autoDismissMs = autoDismissMs,
    )
  }

  private fun launchInterruption(spec: InterruptionSpec) {
    val intent = spec.toIntent().setClass(this, InterruptionActivity::class.java)
    startActivity(intent)
  }
}
