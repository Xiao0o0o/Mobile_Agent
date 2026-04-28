package com.google.androidenv.perturbationhelper

data class InterruptionPreset(
  val id: String,
  val type: InterruptionType,
  val name: String,
  val summary: String,
  val spec: InterruptionSpec,
)
