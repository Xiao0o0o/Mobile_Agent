from __future__ import annotations

import json
import math

from android_world.agents import mobile_agent_utils_new as mobile_agent_utils
from downstream_task.types import DiagnosisResult


def _format_last_action(last_action: dict | None) -> str:
    if not last_action:
        return "No previous action."
    try:
        return json.dumps(last_action, ensure_ascii=False)
    except Exception:
        return str(last_action)


def _format_last_summary(last_summary: str | None) -> str:
    if not last_summary:
        return "No previous action summary."
    return last_summary.strip()


def _format_last_thought(last_thought: str | None) -> str:
    if not last_thought:
        return "No previous action thought."
    return last_thought.strip()


def _format_recent_history(stage2_history: str) -> str:
    history = stage2_history.strip()
    if not history:
        return "No previous action history."
    return history


def _format_action_history(recent_actions: list[dict] | None) -> str:
    if not recent_actions:
        return "No previous actions."
    lines = []
    recent_slice = recent_actions[-10:]
    start_idx = len(recent_actions) - len(recent_slice) + 1
    for idx, action in enumerate(recent_slice, start=start_idx):
        try:
            action_text = json.dumps(action, ensure_ascii=False)
        except Exception:
            action_text = str(action)
        lines.append(f"{idx}. {action_text}")
    return "\n".join(lines)


def _format_recovery_target_condition(recovery_target_condition: str | None) -> str:
    if not recovery_target_condition:
        return "No active recovery target."
    return recovery_target_condition.strip()


def _format_recovery_target_kind(recovery_target_kind: str | None) -> str:
    if not recovery_target_kind:
        return "generic"
    return recovery_target_kind.strip()


def _format_recovery_history(recovery_history: list[dict] | None) -> str:
    if not recovery_history:
        return "No prior recovery actions in the current recovery session."
    lines = []
    for item in recovery_history[-5:]:
        lines.append(
            f"- recovery_step={item.get('recovery_step_count', '?')}, "
            f"mode={item.get('recovery_mode', 'unknown')}, "
            f"action={item.get('action_signature', 'unknown')}, "
            f"summary={item.get('recovery_summary', '')}"
        )
    return "\n".join(lines)


def _extract_action_arguments(last_action: dict | None) -> dict:
    if not last_action:
        return {}
    arguments = last_action.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception:
            return {}
    if isinstance(arguments, dict):
        return arguments
    return {}


def _normalize_coord(coord) -> str:
    if not isinstance(coord, (list, tuple)) or len(coord) != 2:
        return "unknown"
    try:
        x = int(math.floor(float(coord[0]) / 20.0) * 20)
        y = int(math.floor(float(coord[1]) / 20.0) * 20)
        return f"{x},{y}"
    except Exception:
        return "unknown"


def _action_signature(action: dict | None) -> str:
    arguments = _extract_action_arguments(action)
    action_type = str(arguments.get("action", "")).strip().lower()
    if not action_type:
        return "unknown"

    if action_type == "type":
        return f"type::{arguments.get('text', '').strip()}"
    if action_type == "system_button":
        return f"system_button::{arguments.get('button', '').strip()}"
    if action_type in {"click", "long_press"}:
        return f"{action_type}::{_normalize_coord(arguments.get('coordinate'))}"
    if action_type == "swipe":
        start = _normalize_coord(arguments.get("coordinate"))
        end = _normalize_coord(arguments.get("coordinate2"))
        return f"swipe::{start}->{end}"
    if action_type == "open_app":
        return f"open_app::{arguments.get('text', '').strip()}"
    if action_type == "wait":
        return f"wait::{arguments.get('time', '')}"
    if action_type == "terminate":
        return f"terminate::{arguments.get('status', '').strip()}"
    return action_type


def _infer_postcondition_from_explanation(text: str) -> str | None:
    normalized = text.strip().lower()
    if not normalized:
        return None

    if any(token in normalized for token in {"dismiss", "close", "resolve"}) and any(
        token in normalized for token in {"dialog", "popup", "warning", "message", "interference"}
    ):
        return "The interfering dialog or popup should be dismissed and the main task UI should become visible again."
    if "app drawer" in normalized:
        return "The app drawer should now be open and app icons should be visible."
    if "open" in normalized and "app" in normalized:
        return "The intended app should now be open and its main UI should be visible."
    if "stop the recording" in normalized or "stop recording" in normalized:
        return "The recording should stop, and a save or rename dialog should appear."
    if "start recording" in normalized or "recording should start" in normalized:
        return "Recording should now be in progress and a stop control should be visible."
    if "save" in normalized and "record" in normalized:
        return "The recording should be saved successfully and the save or rename dialog should close."
    if (
        "clear the existing text" in normalized
        or "delete the existing text" in normalized
        or "clear the field" in normalized
        or "remove the old name" in normalized
    ):
        return (
            "The old text in the target input field should be removed, or the field should be fully selected and ready to be replaced."
        )
    if "select all" in normalized or "select the text" in normalized or "selection" in normalized:
        return "The relevant text should now be selected, or a text-selection menu should be visible."
    if "go back" in normalized or "navigate back" in normalized or "previous screen" in normalized:
        return "The app should return to the previous screen."
    if "home screen" in normalized:
        return "The home screen should now be visible."
    if "enter" in normalized and "text" in normalized:
        return "The target text field should now reflect the newly entered text."
    return None


def build_previous_intended_effect(
    last_action: dict | None,
    last_summary: str | None = None,
    last_thought: str | None = None,
) -> str:
    if not last_action:
        return "No previous intended effect."

    # Current conclusion/thought-first intended-effect construction is kept for
    # reference, but disabled so diagnosis goes back to the older action-type-
    # specific postcondition rules.
    #
    # previous_conclusion = _format_last_summary(last_summary)
    # previous_thought = _format_last_thought(last_thought)
    #
    # if (
    #     previous_conclusion != "No previous action summary."
    #     and previous_thought != "No previous action thought."
    # ):
    #     return (
    #         "Verify whether the current screenshot realizes the previous conclusion below. "
    #         "Use the thought as supporting context for what the main agent was trying to achieve.\n\n"
    #         f"Previous conclusion:\n{previous_conclusion}\n\n"
    #         f"Supporting thought:\n{previous_thought}"
    #     )
    # if previous_conclusion != "No previous action summary.":
    #     return (
    #         "Verify whether the current screenshot realizes the previous conclusion below.\n\n"
    #         f"Previous conclusion:\n{previous_conclusion}"
    #     )
    # if previous_thought != "No previous action thought.":
    #     return (
    #         "Verify whether the current screenshot realizes the result implied by the previous thought below.\n\n"
    #         f"Previous thought:\n{previous_thought}"
    #     )

    arguments = _extract_action_arguments(last_action)
    action_type = str(arguments.get("action", "")).strip().lower()
    explanation = _format_last_thought(last_thought)
    if explanation == "No previous action thought.":
        explanation = _format_last_summary(last_summary)
    if explanation == "No previous action summary.":
        explanation = ""

    if action_type == "type":
        text = str(arguments.get("text", "")).strip()
        if text:
            return (
                f'The target text field should now contain exactly "{text}". '
                "If older text was supposed to be replaced, the older text should no longer be visible."
            )
        return "The target text field should now reflect the newly entered text."

    inferred = _infer_postcondition_from_explanation(explanation)
    if inferred:
        return inferred

    if action_type == "click":
        return (
            "The tapped target should cause the intended UI change. "
            "If the expected next UI does not appear, or the key task state stays the same, the previous step likely failed."
        )
    if action_type == "long_press":
        return "The target element should become selected, or a context menu / text-selection UI should appear."
    if action_type == "swipe":
        return "The page should scroll or transition in the intended direction, revealing new UI content."
    if action_type == "system_button":
        button = str(arguments.get("button", "")).strip()
        if button == "Back":
            return "The app should return to the previous screen."
        if button == "Home":
            return "The home screen should now be visible."
        if button == "Enter":
            return "The current text input should be submitted or confirmed."
        return "The system UI should change according to the pressed system button."
    if action_type == "open_app":
        app_name = str(arguments.get("text", "the target app")).strip() or "the target app"
        return f"{app_name} should now be open and its main UI should be visible."
    if action_type == "wait":
        return "The current UI should have time to update, and any transient loading or delayed response should resolve if it was in progress."
    if action_type == "terminate":
        return "The task should now be complete."
    if action_type == "answer":
        return "The requested answer or result should now be ready to return."

    return (
        "The current screen should reflect the intended result of the previous action. "
        "If the key task state did not change, the previous step may not have worked as expected."
    )


def build_repeated_issue_signal(
    last_action: dict | None,
    recent_actions: list[dict] | None = None,
) -> tuple[str, int]:
    if not last_action or not recent_actions:
        return "No strong repeated-action signal detected.", 0

    target_signature = _action_signature(last_action)
    if target_signature == "unknown":
        return "No strong repeated-action signal detected.", 0

    streak = 0
    for action in reversed(recent_actions):
        if _action_signature(action) != target_signature:
            break
        streak += 1

    if streak >= 2:
        return (
            "Recent repeated-action signal: "
            f"the last {streak} actions were similar attempts with signature `{target_signature}`. "
            "If the current screenshot still violates the previous intended effect, treat this as a repeated unresolved issue."
        ), streak
    return "No strong repeated-action signal detected.", streak


def build_diagnosis_messages(
    goal: str,
    stage2_history: str,
    screenshot_file: str,
    last_action: dict | None = None,
    last_summary: str | None = None,
    last_thought: str | None = None,
    recent_actions: list[dict] | None = None,
    recovery_target_condition: str | None = None,
    recovery_target_kind: str | None = None,
    recovery_step_count: int = 0,
    recovery_history: list[dict] | None = None,
    recovery_active: bool = False,
):
    previous_intended_effect = build_previous_intended_effect(
        last_action=last_action,
        last_summary=last_summary,
        last_thought=last_thought,
    )
    recent_action_history = _format_action_history(recent_actions)
    system_text = (
        "You are a mobile UI state diagnosis assistant. "
        "Before the task agent acts, inspect the current screenshot and decide "
        "whether the previous step succeeded, whether the agent is stuck, and whether recovery is needed.\n\n"
        "Focus on four questions:\n"
        "1. Is there interference or an off-task overlay/page that should be resolved first?\n"
        "2. Is the screen currently loading, delayed, or unresponsive?\n"
        "3. Does the current screenshot realize the previous conclusion together with the previous intended effect?\n"
        "4. Does the recent action history suggest the agent is stuck repeating the same unresolved step?\n\n"
        "Return JSON only with these exact keys:\n"
        "{\n"
        '  "interference_present": true/false,\n'
        '  "screen_status": "responsive" | "loading" | "unresponsive" | "uncertain",\n'
        '  "previous_step_status": "as_expected" | "no_effect" | "unexpected_effect" | "uncertain",\n'
        '  "task_alignment": "on_track" | "off_track" | "uncertain",\n'
        '  "previous_intended_effect_satisfied": "yes" | "no" | "uncertain",\n'
        '  "recovery_target_resolved": "yes" | "no" | "uncertain",\n'
        '  "repeat_failure_detected": true/false,\n'
        '  "same_issue_streak": non-negative integer,\n'
        '  "need_recovery": true/false,\n'
        '  "recovery_mode": "continue" | "dismiss_interference" | "wait" | "backtrack" | "reopen_context" | "alternative_action",\n'
        '  "reason": "short explanation"\n'
        "}\n"
        "Be conservative: only mark need_recovery=true when the screenshot strongly suggests the task should not continue normally. "
        "Explicitly compare the screenshot against the previous conclusion and the previous intended effect. "
        "Only use `no` for previous_intended_effect_satisfied when the current UI clearly shows that the previous conclusion or intended effect did not happen, was contradicted, or failed to take effect. "
        "If the intended effect is not visible, do not mark previous_step_status as `as_expected`. "
        "If the recent action history shows the same unresolved step repeating, prefer repeat_failure_detected=true. "
        "If a recovery target is provided, only mark recovery_target_resolved as `yes` when the screenshot directly satisfies that target."
    )

    user_text = (
        "Diagnose whether the current page needs recovery before normal task execution.\n\n"
        + f"Main task goal:\n{goal}\n\n"
        + f"Recent action history:\n{recent_action_history}\n\n"
        + f"Previous action:\n{_format_last_action(last_action)}\n\n"
        + f"Previous action conclusion:\n{_format_last_summary(last_summary)}\n\n"
        + f"Previous intended effect:\n{previous_intended_effect}\n\n"
        + (
            f"Active recovery target:\n{_format_recovery_target_condition(recovery_target_condition)}\n\n"
            if recovery_active
            else ""
        )
        + "Use the attached screenshot as the primary evidence. "
        + "Do not propose a full task action here; only decide whether recovery is needed."
    )

    return [
        {"role": "system", "content": [{"text": system_text}]},
        {
            "role": "user",
            "content": [
                {"text": user_text},
                {"image": screenshot_file},
            ],
        },
    ]


def build_recovery_messages(
    goal: str,
    stage2_history: str,
    screenshot_file: str,
    diagnosis: DiagnosisResult,
    resized_width: int,
    resized_height: int,
    last_action: dict | None = None,
    last_summary: str | None = None,
    last_thought: str | None = None,
    recent_actions: list[dict] | None = None,
    recovery_target_condition: str | None = None,
    recovery_target_kind: str | None = None,
    recovery_step_count: int = 0,
    recovery_history: list[dict] | None = None,
):
    recovery_target_text = _format_recovery_target_condition(recovery_target_condition)
    specific_failure_text = diagnosis.reason or "The previous step did not achieve its intended effect."
    action_history_text = _format_action_history(recent_actions)
    final_diagnosis_text = json.dumps(
        {
            "interference_present": diagnosis.interference_present,
            "screen_status": diagnosis.screen_status,
            "previous_step_status": diagnosis.previous_step_status,
            "task_alignment": diagnosis.task_alignment,
            "previous_intended_effect_satisfied": diagnosis.previous_intended_effect_satisfied,
            "recovery_target_resolved": diagnosis.recovery_target_resolved,
            "repeat_failure_detected": diagnosis.repeat_failure_detected,
            "same_issue_streak": diagnosis.same_issue_streak,
            "need_recovery": diagnosis.need_recovery,
            "recovery_mode": diagnosis.recovery_mode,
            "reason": diagnosis.reason,
        },
        ensure_ascii=False,
        indent=2,
    )

    diagnosis_guidance = []
    if diagnosis.interference_present:
        diagnosis_guidance.append(
            "- The diagnosis suggests there is interference on the page. Prioritize dismissing, resolving, or getting past the interfering UI before resuming the main task."
        )
    if diagnosis.screen_status == "loading":
        diagnosis_guidance.append(
            "- The diagnosis suggests the page may still be loading or delayed. A `wait` action is appropriate if the UI appears transient or in progress."
        )
    elif diagnosis.screen_status == "unresponsive":
        diagnosis_guidance.append(
            "- The diagnosis suggests the page may be unresponsive. You may try `wait` first if the page may still recover, but if a stable blocking state is visible, choose a stronger corrective action."
        )
    if diagnosis.previous_step_status in {"no_effect", "unexpected_effect"}:
        diagnosis_guidance.append(
            "- The previous step did not work as expected. Do not blindly repeat the exact same move. Prefer a different visible target, different coordinate, or a different route to recover."
        )
    if diagnosis.repeat_failure_detected or diagnosis.same_issue_streak >= 2:
        diagnosis_guidance.append(
            "- The same underlying issue appears to have persisted across repeated similar attempts. Do not repeat the same action pattern again; choose a different corrective strategy."
        )
    if diagnosis.recovery_target_resolved == "no":
        diagnosis_guidance.append(
            "- The broader recovery target is not yet resolved. Even if the most recent recovery action partially worked, continue recovery until the overall target condition is satisfied."
        )
    if diagnosis.task_alignment == "off_track":
        diagnosis_guidance.append(
            "- The current page seems off the main task path. Prefer the shortest action that returns to the correct task context."
        )
    if recovery_target_kind == "local_postcondition":
        diagnosis_guidance.append(
            "- This recovery session is for fixing the diagnosed problem described in the recovery target condition. Stay focused on that problem."
        )
        diagnosis_guidance.append(
            "- Do not restart or broaden the workflow unless the current UI is blocked, missing, or clearly unusable."
        )
    elif recovery_target_kind == "interference":
        diagnosis_guidance.append(
            "- This recovery session is only for dismissing or resolving the current interference. Once the interference is gone, the main agent will resume."
        )
    elif recovery_target_kind == "task_context":
        diagnosis_guidance.append(
            "- This recovery session is only for returning to the correct task context, not for completing the whole task."
        )
    if not diagnosis_guidance:
        diagnosis_guidance.append(
            "- Choose the single minimal recovery action that best restores a healthy task state."
        )

    recovery_goal = (
        "You are a recovery assistant for a mobile UI task agent.\n"
        "Keep the overall task goal in mind, but do not take over full task planning.\n"
        "Your job is to repair the current failure so that the main agent can continue.\n"
        "Prefer fixing the current diagnosed problem first.\n"
        "If the same repair action has already failed multiple times, choose a different corrective action that still serves the same immediate objective.\n"
        "Only broaden to a larger task context if the current UI is blocked, unusable, or cannot solve the diagnosed problem.\n"
        "Output exactly one recovery action."
    )
    recovery_add_info = (
        "You are not selecting the normal next task action. "
        "You are selecting one recovery action to help the main agent continue.\n"
        f"Main task goal:\n{goal}\n\n"
        f"Previous conclusion / summary:\n{_format_last_summary(last_summary)}\n\n"
        f"Specific problem to repair now:\n{specific_failure_text}\n\n"
        f"Final diagnosis for this step:\n{final_diagnosis_text}\n\n"
        f"Recent action history:\n{action_history_text}\n\n"
        f"Previous action:\n{_format_last_action(last_action)}\n\n"
        f"Recovery success condition:\n{recovery_target_text}\n\n"
        "Constraints:\n"
        "- Do not restart the whole task.\n"
        "- Do not abandon the current subtask unless the current UI is blocked or unusable.\n"
        "- If a repeated recovery attempt did not change the UI, choose a different corrective tactic.\n"
        "- Prefer the smallest action that repairs the problem and still supports the main task.\n"
        "- Stay close to the current task context whenever possible.\n"
        "- Use the previous thought and conclusion as guidance for what the main agent was trying to finish.\n"
        "Recovery guidance:\n"
        + "\n".join(diagnosis_guidance)
        + "\n"
        "- Prefer actions that move the recovery state forward. Avoid repeating the exact same recovery action if it already failed or only produced an intermediate state.\n"
        "- If a simple `wait` is unlikely to change the current page, choose a more direct recovery action instead of waiting again.\n"
        "- If the diagnosed problem has already been solved, stop broadening the recovery plan; the normal task agent will resume automatically.\n"
        "- Keep the action minimal and recovery-oriented."
    )

    system_prompt_part, user_prompt_part = mobile_agent_utils.build_system_messages(
        recovery_goal,
        resized_width,
        resized_height,
        recovery_add_info,
        action_history_text,
    )
    user_prompt_part["content"].append({"image": screenshot_file})
    return [system_prompt_part, user_prompt_part]
