from __future__ import annotations

import json

from downstream_task.prompts import build_recovery_messages
from downstream_task.types import DiagnosisResult


def _extract_tool_call_payload(action_response: str):
    thought = None
    summary = None

    if "<think>" in action_response and "</think>" in action_response:
        thought = action_response.split("<think>", 1)[1].split("</think>", 1)[0].strip()
    elif "<thinking>" in action_response and "</thinking>" in action_response:
        thought = (
            action_response.split("<thinking>", 1)[1]
            .split("</thinking>", 1)[0]
            .strip()
        )

    dummy_action = (
        '{"name": "mobile_use"'
        + action_response.split('{"name": "mobile_use"', 1)[1].split("}}\n", 1)[0]
        + "}}"
    )
    if "<conclusion>" in action_response and "</conclusion>" in action_response:
        summary = (
            action_response.split("<conclusion>", 1)[1]
            .split("</conclusion>", 1)[0]
            .strip()
        )

    parsed_action = json.loads(dummy_action)
    parsed_action["arguments"]["action"] = parsed_action["arguments"]["action"].replace(
        "tap", "click"
    )
    if summary is None:
        action_name = parsed_action.get("arguments", {}).get("action", "unknown")
        summary = f"Recovery action: {action_name}"
    return parsed_action, thought, summary

def run_recovery_prompt(
    vllm,
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
    messages = build_recovery_messages(
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
        recovery_target_condition=recovery_target_condition,
        recovery_target_kind=recovery_target_kind,
        recovery_step_count=recovery_step_count,
        recovery_history=recovery_history,
    )
    response_text, _, _ = vllm.predict_mm("", [], messages=messages)
    dummy_action, thought, summary = _extract_tool_call_payload(response_text)
    return dummy_action, thought, summary, response_text
