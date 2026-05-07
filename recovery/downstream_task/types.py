from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any


SCREEN_STATUSES = {"responsive", "loading", "unresponsive", "uncertain"}
PREVIOUS_STEP_STATUSES = {
    "as_expected",
    "no_effect",
    "unexpected_effect",
    "uncertain",
}
TASK_ALIGNMENT_STATES = {"on_track", "off_track", "uncertain"}
SATISFACTION_STATES = {"yes", "no", "uncertain"}
RECOVERY_MODES = {
    "continue",
    "dismiss_interference",
    "wait",
    "backtrack",
    "reopen_context",
    "alternative_action",
}
RECOVERY_TARGET_KINDS = {
    "generic",
    "interference",
    "screen_status",
    "local_postcondition",
    "task_context",
}


@dataclass
class DownstreamTaskConfig:
    enabled: bool = False
    log_enable: bool = True
    use_recovery_prompt: bool = True
    wait_seconds: float = 3.0
    recovery_max_steps: int = 3
    hard_stuck_window: int = 5


@dataclass
class DiagnosisResult:
    interference_present: bool = False
    screen_status: str = "uncertain"
    previous_step_status: str = "uncertain"
    task_alignment: str = "uncertain"
    previous_intended_effect_satisfied: str = "uncertain"
    recovery_target_resolved: str = "uncertain"
    repeat_failure_detected: bool = False
    same_issue_streak: int = 0
    need_recovery: bool = False
    recovery_mode: str = "continue"
    reason: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoverySessionState:
    active: bool = False
    session_id: int = 0
    trigger_step: int = -1
    trigger_reason: str = ""
    trigger_recovery_mode: str = "continue"
    target_kind: str = "generic"
    target_condition: str = ""
    recovery_step_count: int = 0
    max_steps: int = 3
    last_exit_reason: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PreActionInterventionResult:
    step_idx: int = -1
    diagnosis: DiagnosisResult | None = None
    diagnosis_raw_response: str = ""
    previous_intended_effect: str = ""
    should_execute_recovery: bool = False
    recovery_mode: str = "continue"
    recovery_raw_response: str = ""
    recovery_dummy_action: dict[str, Any] | None = None
    recovery_summary: str = ""
    recovery_thought: str | None = None
    recovery_session_id: int = 0
    recovery_session_active: bool = False
    recovery_session_step_count: int = 0
    recovery_session_status: str = "inactive"
    recovery_session_exit_reason: str = ""
    recovery_target_kind: str = "generic"
    recovery_target_condition: str = ""
