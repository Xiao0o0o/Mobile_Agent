"""Tests for helper-app launch utilities."""

from __future__ import annotations

import unittest

from mdp_perturbation.helper_app import HelperInterruptionSpec


class HelperInterruptionSpecTest(unittest.TestCase):

  def test_builds_intent_extras(self):
    spec = HelperInterruptionSpec(
        kind="notification",
        title="New message",
        message="Alex: Are you free at 3 PM?",
        app_name="Messages",
        primary_button="Open",
        secondary_button="Dismiss",
        blocking=False,
        auto_dismiss_ms=2500,
        instance_id="case-001",
    )

    self.assertEqual(
        spec.to_intent_extras(),
        {
            "kind": "notification",
            "surface_style": "banner",
            "title": "New message",
            "message": "Alex: Are you free at 3 PM?",
            "app_name": "Messages",
            "primary_button": "Open",
            "secondary_button": "Dismiss",
            "blocking": False,
            "auto_dismiss_ms": ("long", 2500),
            "primary_action": "open_destination",
            "secondary_action": "dismiss",
            "primary_destination": "message_thread",
            "instance_id": "case-001",
        },
    )

  def test_serializes_destination_actions(self):
    spec = HelperInterruptionSpec(
        kind="ad",
        title="48-hour flash sale",
        primary_button="Shop now",
        secondary_button="Maybe later",
        primary_action="open_destination",
        primary_destination="shopping_amazon",
        secondary_action="dismiss",
        instance_id="case-002",
    )

    self.assertEqual(
        spec.to_intent_extras(),
        {
            "kind": "ad",
            "surface_style": "interstitial",
            "title": "48-hour flash sale",
            "primary_button": "Shop now",
            "secondary_button": "Maybe later",
            "blocking": True,
            "auto_dismiss_ms": ("long", 0),
            "primary_action": "open_destination",
            "secondary_action": "dismiss",
            "primary_destination": "shopping_amazon",
            "instance_id": "case-002",
        },
    )

  def test_infers_system_update_destination(self):
    spec = HelperInterruptionSpec(
        kind="update",
        app_name="System updater",
        title="Update available",
        primary_button="Update now",
        secondary_button="Later",
        instance_id="case-003",
    )

    self.assertEqual(
        spec.to_intent_extras(),
        {
            "kind": "update",
            "surface_style": "dialog",
            "title": "Update available",
            "app_name": "System updater",
            "primary_button": "Update now",
            "secondary_button": "Later",
            "blocking": True,
            "auto_dismiss_ms": ("long", 0),
            "primary_action": "open_destination",
            "secondary_action": "dismiss",
            "primary_destination": "system_update_settings",
            "instance_id": "case-003",
        },
    )

  def test_preserves_explicit_dismiss(self):
    spec = HelperInterruptionSpec(
        kind="popup",
        app_name="Notes Pro",
        title="Enjoying Notes Pro?",
        primary_button="Rate now",
        secondary_button="No thanks",
        primary_action="dismiss",
        instance_id="case-004",
    )

    self.assertEqual(
        spec.to_intent_extras(),
        {
            "kind": "popup",
            "surface_style": "dialog",
            "title": "Enjoying Notes Pro?",
            "app_name": "Notes Pro",
            "primary_button": "Rate now",
            "secondary_button": "No thanks",
            "blocking": True,
            "auto_dismiss_ms": ("long", 0),
            "primary_action": "dismiss",
            "secondary_action": "dismiss",
            "instance_id": "case-004",
        },
    )

  def test_rejects_unknown_kind(self):
    with self.assertRaises(ValueError):
      HelperInterruptionSpec(kind="toast")


if __name__ == "__main__":
  unittest.main()
