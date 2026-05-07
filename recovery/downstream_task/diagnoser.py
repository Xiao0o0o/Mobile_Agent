from __future__ import annotations

import json

from downstream_task.prompts import build_diagnosis_messages
from downstream_task.types import (
    DiagnosisResult,
    PREVIOUS_STEP_STATUSES,
    RECOVERY_MODES,
    SATISFACTION_STATES,
    SCREEN_STATUSES,
    TASK_ALIGNMENT_STATES,
)


def _extract_first_json_object(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found in diagnosis response.")
    depth = 0
    for idx in range(start, len(text)):
        ch = text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : idx + 1])
    raise ValueError("Unterminated JSON object in diagnosis response.")


def _normalize_enum(value: str, allowed: set[str], default: str) -> str:
    if not isinstance(value, str):
        return default
    normalized = value.strip().lower().replace(" ", "_")
    if normalized in allowed:
        return normalized
    return default


def _normalize_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n", ""}:
            return False
    return default


def _normalize_nonnegative_int(value, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return default
        try:
            return max(0, int(float(normalized)))
        except ValueError:
            return default
    return default


def run_pre_action_diagnosis(
    vllm,
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
) -> tuple[DiagnosisResult, str]:
    messages = build_diagnosis_messages(
        goal=goal,
        stage2_history=stage2_history,
        screenshot_file=screenshot_file,
        last_action=last_action,
        last_summary=last_summary,
        last_thought=last_thought,
        recent_actions=recent_actions,
        recovery_target_condition=recovery_target_condition,
        recovery_target_kind=recovery_target_kind,
        recovery_step_count=recovery_step_count,
        recovery_history=recovery_history,
        recovery_active=recovery_active,
    )
    response_text, _, _ = vllm.predict_mm("", [], messages=messages)
    parsed = _extract_first_json_object(response_text)

    diagnosis = DiagnosisResult(
        interference_present=_normalize_bool(
            parsed.get("interference_present", False),
            default=False,
        ),
        screen_status=_normalize_enum(
            parsed.get("screen_status", "uncertain"),
            SCREEN_STATUSES,
            "uncertain",
        ),
        previous_step_status=_normalize_enum(
            parsed.get("previous_step_status", "uncertain"),
            PREVIOUS_STEP_STATUSES,
            "uncertain",
        ),
        task_alignment=_normalize_enum(
            parsed.get("task_alignment", "uncertain"),
            TASK_ALIGNMENT_STATES,
            "uncertain",
        ),
        previous_intended_effect_satisfied=_normalize_enum(
            parsed.get("previous_intended_effect_satisfied", "uncertain"),
            SATISFACTION_STATES,
            "uncertain",
        ),
        recovery_target_resolved=_normalize_enum(
            parsed.get("recovery_target_resolved", "uncertain"),
            SATISFACTION_STATES,
            "uncertain",
        ),
        repeat_failure_detected=_normalize_bool(
            parsed.get("repeat_failure_detected", False),
            default=False,
        ),
        same_issue_streak=_normalize_nonnegative_int(
            parsed.get("same_issue_streak", 0),
            default=0,
        ),
        need_recovery=_normalize_bool(
            parsed.get("need_recovery", False),
            default=False,
        ),
        recovery_mode=_normalize_enum(
            parsed.get("recovery_mode", "continue"),
            RECOVERY_MODES,
            "continue",
        ),
        reason=str(parsed.get("reason", "")).strip(),
        raw=parsed,
    )
    return diagnosis, response_text
