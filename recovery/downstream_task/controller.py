from __future__ import annotations

import json
import os
from dataclasses import asdict

from downstream_task.diagnoser import run_pre_action_diagnosis
from downstream_task.prompts import build_previous_intended_effect
from downstream_task.recovery import run_recovery_prompt
from downstream_task.types import DownstreamTaskConfig
from downstream_task.types import PreActionInterventionResult
from downstream_task.types import RecoverySessionState


def _append_jsonl(path: str, payload: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _log_diagnosis(
    task_output_dir: str | None,
    step_idx: int,
    intervention: PreActionInterventionResult,
):
    if not task_output_dir or intervention.diagnosis is None:
        return
    _append_jsonl(
        os.path.join(task_output_dir, "diagnosis.jsonl"),
        {
            "step": step_idx,
            "diagnosis_raw_response": intervention.diagnosis_raw_response,
            "diagnosis": asdict(intervention.diagnosis),
            "previous_intended_effect": intervention.previous_intended_effect,
            "recovery_session_id": intervention.recovery_session_id,
            "recovery_session_active": intervention.recovery_session_active,
            "recovery_session_step_count": intervention.recovery_session_step_count,
            "recovery_session_status": intervention.recovery_session_status,
            "recovery_session_exit_reason": intervention.recovery_session_exit_reason,
            "recovery_target_kind": intervention.recovery_target_kind,
            "recovery_target_condition": intervention.recovery_target_condition,
        },
    )


def _log_recovery(
    task_output_dir: str | None,
    step_idx: int,
    intervention: PreActionInterventionResult,
):
    if not task_output_dir or not intervention.should_execute_recovery:
        return
    _append_jsonl(
        os.path.join(task_output_dir, "recovery.jsonl"),
        {
            "step": step_idx,
            "recovery_mode": intervention.recovery_mode,
            "recovery_raw_response": intervention.recovery_raw_response,
            "recovery_dummy_action": intervention.recovery_dummy_action,
            "recovery_summary": intervention.recovery_summary,
            "recovery_session_id": intervention.recovery_session_id,
            "recovery_session_step_count": intervention.recovery_session_step_count,
            "recovery_session_status": intervention.recovery_session_status,
            "recovery_target_kind": intervention.recovery_target_kind,
            "recovery_target_condition": intervention.recovery_target_condition,
        },
    )


def _is_meaningful_intended_effect(previous_intended_effect: str) -> bool:
    normalized = (previous_intended_effect or "").strip()
    return bool(normalized) and normalized != "No previous intended effect."


def _normalize_stuck_text(text: str | None) -> str:
    return " ".join((text or "").split())


def _serialize_action_for_stuck(action: dict | None) -> str:
    try:
        return json.dumps(action or {}, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(action)


def _detect_hard_stuck_pattern(
    recent_actions: list[dict] | None,
    recent_summaries: list[str | None] | None,
    recent_thoughts: list[str | None] | None,
    *,
    window: int,
) -> dict | None:
    if window <= 1:
        return None
    if not recent_actions or not recent_summaries or not recent_thoughts:
        return None
    if (
        len(recent_actions) < window
        or len(recent_summaries) < window
        or len(recent_thoughts) < window
    ):
        return None

    action_window = recent_actions[-window:]
    summary_window = recent_summaries[-window:]
    thought_window = recent_thoughts[-window:]

    action_key = _serialize_action_for_stuck(action_window[-1])
    summary_key = _normalize_stuck_text(summary_window[-1])
    thought_key = _normalize_stuck_text(thought_window[-1])

    if not summary_key or not thought_key:
        return None

    if any(_serialize_action_for_stuck(action) != action_key for action in action_window):
        return None
    if any(_normalize_stuck_text(summary) != summary_key for summary in summary_window):
        return None
    if any(_normalize_stuck_text(thought) != thought_key for thought in thought_window):
        return None

    return {
        "window": window,
        "action": action_key,
        "summary": summary_key,
        "thought": thought_key,
    }


def _apply_hard_stuck_override(
    intervention: PreActionInterventionResult,
    hard_stuck_info: dict | None,
):
    if hard_stuck_info is None or intervention.diagnosis is None:
        return

    diagnosis = intervention.diagnosis
    window = int(hard_stuck_info["window"])
    diagnosis.previous_step_status = "no_effect"
    diagnosis.previous_intended_effect_satisfied = "no"
    diagnosis.recovery_target_resolved = "no"
    diagnosis.repeat_failure_detected = True
    diagnosis.same_issue_streak = max(diagnosis.same_issue_streak, window)
    diagnosis.need_recovery = True
    diagnosis.recovery_mode = "alternative_action"
    diagnosis.task_alignment = "off_track"

    reason = (
        f"Hard stuck rule triggered: the last {window} completed steps had identical "
        "action, thought, and summary, so the previous intended effect likely did not execute correctly."
    )
    if diagnosis.reason:
        diagnosis.reason = reason + " " + diagnosis.reason
    else:
        diagnosis.reason = reason


def _derive_recovery_mode(intervention: PreActionInterventionResult) -> str:
    diagnosis = intervention.diagnosis
    if diagnosis is None:
        return "continue"

    target_kind = intervention.recovery_target_kind
    if intervention.recovery_session_active and target_kind == "local_postcondition":
        if diagnosis.interference_present:
            return "dismiss_interference"
        if diagnosis.screen_status in {"loading", "unresponsive"}:
            return "wait"
        if diagnosis.previous_intended_effect_satisfied == "yes":
            return "continue"
        return "alternative_action"
    if intervention.recovery_session_active and target_kind == "interference":
        if diagnosis.interference_present:
            return "dismiss_interference"
        return "continue"
    if intervention.recovery_session_active and target_kind == "screen_status":
        if diagnosis.screen_status in {"loading", "unresponsive"}:
            return "wait"
        return "continue"
    if intervention.recovery_session_active and target_kind == "task_context":
        if diagnosis.interference_present:
            return "dismiss_interference"
        if diagnosis.screen_status in {"loading", "unresponsive"}:
            return "wait"
        if diagnosis.task_alignment == "off_track":
            return "backtrack"
        return "continue"

    if diagnosis.recovery_mode != "continue":
        return diagnosis.recovery_mode

    if diagnosis.screen_status in {"loading", "unresponsive"}:
        return "wait"
    if diagnosis.interference_present:
        return "dismiss_interference"
    if (
        _is_meaningful_intended_effect(intervention.previous_intended_effect)
        and diagnosis.previous_intended_effect_satisfied == "no"
    ):
        return "alternative_action"
    if diagnosis.repeat_failure_detected or diagnosis.same_issue_streak >= 2:
        return "alternative_action"
    return "continue"


def _should_trigger_recovery(intervention: PreActionInterventionResult) -> tuple[bool, str]:
    diagnosis = intervention.diagnosis
    if diagnosis is None:
        return False, "continue"

    recovery_mode = _derive_recovery_mode(intervention)
    step_idx = intervention.step_idx

    if step_idx == 0:
        return False, "continue"

    signal_present = (
        diagnosis.interference_present
        or diagnosis.screen_status in {"loading", "unresponsive"}
        or (
            _is_meaningful_intended_effect(intervention.previous_intended_effect)
            and diagnosis.previous_intended_effect_satisfied == "no"
        )
        or diagnosis.repeat_failure_detected
        or diagnosis.same_issue_streak >= 2
    )
    if signal_present and recovery_mode != "continue":
        reason_prefix = "Recovery triggered by fallback signals: "
        if diagnosis.reason:
            diagnosis.reason = reason_prefix + diagnosis.reason
        else:
            diagnosis.reason = reason_prefix + (
                f"screen_status={diagnosis.screen_status}, "
                f"task_alignment={diagnosis.task_alignment}, "
                f"previous_step_status={diagnosis.previous_step_status}, "
                f"previous_intended_effect_satisfied={diagnosis.previous_intended_effect_satisfied}, "
                f"interference_present={diagnosis.interference_present}, "
                f"repeat_failure_detected={diagnosis.repeat_failure_detected}, "
                f"same_issue_streak={diagnosis.same_issue_streak}"
            )
        return True, recovery_mode
    return False, "continue"


def _derive_recovery_target(
    intervention: PreActionInterventionResult,
) -> tuple[str, str]:
    diagnosis = intervention.diagnosis
    if diagnosis is None:
        return (
            "generic",
            "The device should return to a healthy state where the main task can continue safely.",
        )

    meaningful_intended_effect = _is_meaningful_intended_effect(
        intervention.previous_intended_effect
    )
    local_repair_needed = meaningful_intended_effect and (
        diagnosis.previous_intended_effect_satisfied == "no"
        or diagnosis.repeat_failure_detected
        or diagnosis.same_issue_streak >= 2
    )

    if diagnosis.interference_present:
        return (
            "interference",
            "Any interfering dialog, popup, or overlay should be dismissed so the underlying task UI is visible again.",
        )
    if diagnosis.screen_status in {"loading", "unresponsive"}:
        return ("screen_status", "The current screen should become stable and responsive again.")
    if local_repair_needed:
        return ("local_postcondition", intervention.previous_intended_effect)
    if diagnosis.task_alignment == "off_track":
        return (
            "task_context",
            "The interface should return to the correct task path before normal execution resumes.",
        )
    if meaningful_intended_effect:
        return ("local_postcondition", intervention.previous_intended_effect)
    return (
        "generic",
        "The device should return to a healthy state where the main task can continue safely.",
    )


def _populate_session_metadata(
    intervention: PreActionInterventionResult,
    recovery_session: RecoverySessionState | None,
):
    if recovery_session is None:
        return
    intervention.recovery_session_id = recovery_session.session_id
    intervention.recovery_session_active = recovery_session.active
    intervention.recovery_session_step_count = recovery_session.recovery_step_count
    intervention.recovery_target_kind = recovery_session.target_kind
    intervention.recovery_target_condition = recovery_session.target_condition


def _start_recovery_session(
    recovery_session: RecoverySessionState,
    *,
    step_idx: int,
    intervention: PreActionInterventionResult,
    recovery_mode: str,
    config: DownstreamTaskConfig,
):
    recovery_session.active = True
    recovery_session.session_id += 1
    recovery_session.trigger_step = step_idx
    recovery_session.trigger_reason = intervention.diagnosis.reason if intervention.diagnosis else ""
    recovery_session.trigger_recovery_mode = recovery_mode
    (
        recovery_session.target_kind,
        recovery_session.target_condition,
    ) = _derive_recovery_target(intervention)
    recovery_session.recovery_step_count = 0
    recovery_session.max_steps = max(1, int(config.recovery_max_steps))
    recovery_session.last_exit_reason = ""
    recovery_session.history = []


def _close_recovery_session(
    recovery_session: RecoverySessionState,
    *,
    exit_reason: str,
):
    recovery_session.active = False
    recovery_session.last_exit_reason = exit_reason
    recovery_session.history = []
    recovery_session.recovery_step_count = 0
    recovery_session.trigger_step = -1
    recovery_session.trigger_reason = ""
    recovery_session.trigger_recovery_mode = "continue"
    recovery_session.target_kind = "generic"
    recovery_session.target_condition = ""

def _refresh_recovery_target_if_needed(
    recovery_session: RecoverySessionState,
    intervention: PreActionInterventionResult,
):
    # Keep the recovery target locked to the specific problem that triggered
    # this recovery session. Only fill it in if it is unexpectedly empty.
    if recovery_session.target_condition:
        return
    recovery_session.target_kind, recovery_session.target_condition = _derive_recovery_target(
        intervention
    )


def _is_recovery_resolved(
    intervention: PreActionInterventionResult,
) -> bool:
    diagnosis = intervention.diagnosis
    if diagnosis is None:
        return False
    target_kind = intervention.recovery_target_kind
    if target_kind == "local_postcondition":
        if diagnosis.previous_intended_effect_satisfied == "yes":
            return True
        if diagnosis.previous_intended_effect_satisfied == "no":
            return False
        return diagnosis.recovery_target_resolved == "yes"
    if target_kind == "interference":
        if diagnosis.interference_present:
            return False
        if diagnosis.recovery_target_resolved == "no":
            return False
        return True
    if target_kind == "screen_status":
        if diagnosis.screen_status in {"loading", "unresponsive"}:
            return False
        if diagnosis.recovery_target_resolved == "no":
            return False
        return True
    if target_kind == "task_context":
        if diagnosis.task_alignment == "off_track":
            return False
        if diagnosis.recovery_target_resolved == "no":
            return False
        return True
    if diagnosis.recovery_target_resolved == "yes":
        return True
    if diagnosis.recovery_target_resolved == "no":
        return False
    return (
        not diagnosis.need_recovery
        and not diagnosis.interference_present
        and diagnosis.screen_status not in {"loading", "unresponsive"}
        and diagnosis.previous_step_status not in {"no_effect", "unexpected_effect"}
        and diagnosis.task_alignment != "off_track"
        and not diagnosis.repeat_failure_detected
        and diagnosis.same_issue_streak < 2
    )


def _record_recovery_step(
    recovery_session: RecoverySessionState,
    intervention: PreActionInterventionResult,
):
    recovery_session.recovery_step_count += 1
    recovery_session.history.append(
        {
            "step": intervention.step_idx,
            "recovery_step_count": recovery_session.recovery_step_count,
            "recovery_mode": intervention.recovery_mode,
            "recovery_summary": intervention.recovery_summary,
            "action_signature": json.dumps(
                intervention.recovery_dummy_action or {}, ensure_ascii=False
            ),
        }
    )


def maybe_apply_pre_action_intervention(
    *,
    config: DownstreamTaskConfig,
    vllm,
    goal: str,
    stage2_history: str,
    screenshot_file: str,
    resized_width: int,
    resized_height: int,
    step_idx: int,
    task_output_dir: str | None = None,
    last_action: dict | None = None,
    last_summary: str | None = None,
    last_thought: str | None = None,
    recent_actions: list[dict] | None = None,
    recent_summaries: list[str | None] | None = None,
    recent_thoughts: list[str | None] | None = None,
    recovery_session: RecoverySessionState | None = None,
) -> PreActionInterventionResult:
    intervention = PreActionInterventionResult(step_idx=step_idx)
    if not config.enabled:
        return intervention

    if recovery_session is not None:
        if recovery_session.max_steps <= 0:
            recovery_session.max_steps = max(1, int(config.recovery_max_steps))
        _populate_session_metadata(intervention, recovery_session)
        intervention.recovery_session_status = (
            "active" if recovery_session.active else "inactive"
        )

    intervention.previous_intended_effect = build_previous_intended_effect(
        last_action=last_action,
        last_summary=last_summary,
        last_thought=last_thought,
    )

    diagnosis, diagnosis_raw = run_pre_action_diagnosis(
        vllm=vllm,
        goal=goal,
        stage2_history=stage2_history,
        screenshot_file=screenshot_file,
        last_action=last_action,
        last_summary=last_summary,
        last_thought=last_thought,
        recent_actions=recent_actions,
        recovery_target_condition=(
            recovery_session.target_condition
            if recovery_session is not None and recovery_session.active
            else None
        ),
        recovery_target_kind=(
            recovery_session.target_kind
            if recovery_session is not None and recovery_session.active
            else None
        ),
        recovery_step_count=(
            recovery_session.recovery_step_count
            if recovery_session is not None and recovery_session.active
            else 0
        ),
        recovery_history=(
            recovery_session.history
            if recovery_session is not None and recovery_session.active
            else None
        ),
        recovery_active=bool(recovery_session is not None and recovery_session.active),
    )
    intervention.diagnosis = diagnosis
    intervention.diagnosis_raw_response = diagnosis_raw

    _apply_hard_stuck_override(
        intervention,
        _detect_hard_stuck_pattern(
            recent_actions=recent_actions,
            recent_summaries=recent_summaries,
            recent_thoughts=recent_thoughts,
            window=max(2, int(config.hard_stuck_window)),
        ),
    )

    if recovery_session is not None and recovery_session.active:
        _refresh_recovery_target_if_needed(recovery_session, intervention)
        _populate_session_metadata(intervention, recovery_session)
        intervention.recovery_session_status = "active"

        if _is_recovery_resolved(intervention):
            _close_recovery_session(recovery_session, exit_reason="resolved")
            _populate_session_metadata(intervention, recovery_session)
            intervention.recovery_session_status = "resolved"
            intervention.recovery_session_exit_reason = "resolved"
            if config.log_enable:
                _log_diagnosis(task_output_dir, step_idx, intervention)
            return intervention

        if recovery_session.recovery_step_count >= recovery_session.max_steps:
            _close_recovery_session(recovery_session, exit_reason="max_steps_reached")
            _populate_session_metadata(intervention, recovery_session)
            intervention.recovery_session_status = "max_steps_reached"
            intervention.recovery_session_exit_reason = "max_steps_reached"
            if config.log_enable:
                _log_diagnosis(task_output_dir, step_idx, intervention)
            return intervention

        resolved_mode = _derive_recovery_mode(intervention)
        if resolved_mode == "continue":
            resolved_mode = "alternative_action"
        intervention.should_execute_recovery = True
        intervention.recovery_mode = resolved_mode
        diagnosis.recovery_mode = resolved_mode
        intervention.recovery_session_status = "continuing"
    else:
        should_recover, resolved_mode = _should_trigger_recovery(intervention)
        if not should_recover:
            if config.log_enable:
                _log_diagnosis(task_output_dir, step_idx, intervention)
            return intervention

        if recovery_session is not None:
            _start_recovery_session(
                recovery_session,
                step_idx=step_idx,
                intervention=intervention,
                recovery_mode=resolved_mode,
                config=config,
            )
            _populate_session_metadata(intervention, recovery_session)
        intervention.should_execute_recovery = True
        intervention.recovery_mode = resolved_mode
        diagnosis.recovery_mode = resolved_mode
        intervention.recovery_session_status = "started"

    if not config.use_recovery_prompt:
        if recovery_session is not None and recovery_session.active:
            _close_recovery_session(
                recovery_session, exit_reason="recovery_prompt_disabled"
            )
            _populate_session_metadata(intervention, recovery_session)
            intervention.recovery_session_status = "recovery_prompt_disabled"
            intervention.recovery_session_exit_reason = "recovery_prompt_disabled"
        intervention.should_execute_recovery = False
        if config.log_enable:
            _log_diagnosis(task_output_dir, step_idx, intervention)
        return intervention

    (
        intervention.recovery_dummy_action,
        intervention.recovery_thought,
        intervention.recovery_summary,
        intervention.recovery_raw_response,
    ) = run_recovery_prompt(
        vllm=vllm,
        goal=goal,
        stage2_history=stage2_history,
        screenshot_file=screenshot_file,
        diagnosis=diagnosis,
        resized_width=resized_width,
        resized_height=resized_height,
        last_action=last_action,
        last_summary=last_summary,
        last_thought=last_thought,
        recent_actions=recent_actions,
        recovery_target_condition=(
            recovery_session.target_condition if recovery_session is not None else None
        ),
        recovery_target_kind=(
            recovery_session.target_kind if recovery_session is not None else None
        ),
        recovery_step_count=(
            (recovery_session.recovery_step_count + 1)
            if recovery_session is not None and recovery_session.active
            else 1
        ),
        recovery_history=(
            recovery_session.history if recovery_session is not None else None
        ),
    )

    if recovery_session is not None and intervention.should_execute_recovery:
        _record_recovery_step(recovery_session, intervention)
        _populate_session_metadata(intervention, recovery_session)

    if config.log_enable:
        _log_diagnosis(task_output_dir, step_idx, intervention)
        _log_recovery(task_output_dir, step_idx, intervention)
    return intervention
