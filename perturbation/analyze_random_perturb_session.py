#!/usr/bin/env python3
"""Analyze a random-perturbation AndroidWorld session.

This script produces:
1. A per-run JSON file with heuristic failure categorization and evidence.
2. A Markdown report with per-task summaries across repeats.

It uses the existing session summary/logs plus the saved episode pkl.gz files so
that each classification can cite concrete terminal UI text and action traces.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
import math
import pickle
import re
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


STATE_PROFILES = {
    "font_size_large",
    "font_size_small",
    "ui_theme_dark",
    "display_size_dpi_compact",
    "display_size_dpi_zoomed_out",
    "orientation_landscape",
    "orientation_toggle",
    "state_reset_home",
    "locale_date_format_us12",
    "locale_date_format_eu24",
}

ACTION_PROFILES = {
    "bottom_sheet_consent",
    "popup_permission",
    "popup_security",
    "interstitial_ad",
    "ad_trial_offer",
    "rate_dialog",
    "update_system",
    "update_app_sheet",
    "notification_message",
    "notification_delivery",
}

TRANSITION_PROFILES = {
    "execution_delay_loading",
    "execution_delay_frozen",
    "partial_loading_skeleton",
    "app_hang_restart_required",
    "action_delay_realistic",
    "action_drop_random",
}


PROFILE_GROUP = {"clean": "baseline"}
PROFILE_GROUP.update({name: "state" for name in STATE_PROFILES})
PROFILE_GROUP.update({name: "action" for name in ACTION_PROFILES})
PROFILE_GROUP.update({name: "transition" for name in TRANSITION_PROFILES})


PROFILE_KEYWORDS = {
    "bottom_sheet_consent": [
        "privacy choices",
        "manage options",
        "manage privacy options",
        "save choices",
        "reject all",
    ],
    "popup_permission": [
        "allow notifications",
        "notification permissions",
        "notification categories",
        "android system notifications",
    ],
    "popup_security": [
        "verify this action",
        "security center",
        "protected action review",
        "risk summary",
        "approve",
    ],
    "interstitial_ad": [
        "flash sale",
        "shop now",
        "amazon shopping",
        "travel gear deals",
        "add to cart",
    ],
    "ad_trial_offer": [
        "premium",
        "install",
        "app store",
        "available updates",
        "maps go update",
    ],
    "rate_dialog": ["enjoying notes pro", "rate now", "rate this app", "submit"],
    "update_system": [
        "update available",
        "system update",
        "download and install",
        "settings / system / system update",
    ],
    "update_app_sheet": [
        "new features are ready",
        "app store",
        "maps go update",
        "view all updates",
    ],
    "notification_message": [
        "new message",
        "messages / jordan",
        "unread attachments",
        "reply",
    ],
    "notification_delivery": [
        "driver is nearby",
        "parcel tracker / delivery",
        "order #4419",
        "open map",
    ],
    "execution_delay_loading": ["loading"],
    "execution_delay_frozen": [
        "isn't responding",
        "taking longer than usual",
        "wait",
        "close app",
    ],
    "partial_loading_skeleton": ["loading content"],
    "app_hang_restart_required": [
        "isn't responding",
        "restart app",
        "close app",
    ],
}


REASON_FAMILY = {
    "success": "success",
    "runtime_exception_before_eval": "exception",
    "partial_success": "task_intrinsic_or_general",
    "declared_done_but_overlay_or_popup_still_interfering": "action_perturbation",
    "declared_done_but_exact_target_not_met": "task_intrinsic_or_general",
    "declared_done_but_wrong_end_state": "task_intrinsic_or_general",
    "failed_to_recover_after_state_reset": "state_perturbation",
    "interruption_not_cleared_or_wrongly_ignored": "action_perturbation",
    "misread_delayed_transition_or_loading_state": "transition_perturbation",
    "looping_under_interruption": "action_perturbation",
    "looping_after_transition_perturbation": "transition_perturbation",
    "looping_after_state_or_layout_shift": "state_perturbation",
    "state_or_layout_shift_confusion": "state_perturbation",
    "task_loop": "task_intrinsic_or_general",
    "task_progress_stalled": "task_intrinsic_or_general",
    "unknown_eval": "exception",
}


REASON_CN = {
    "success": "成功",
    "runtime_exception_before_eval": "运行时异常，任务在评测前中断",
    "partial_success": "部分完成，但最终状态没有完全满足任务",
    "declared_done_but_overlay_or_popup_still_interfering": "agent 提前宣告完成，但弹窗/覆盖层仍在干扰",
    "declared_done_but_exact_target_not_met": "agent 提前宣告完成，但没有满足精确目标",
    "declared_done_but_wrong_end_state": "agent 提前宣告完成，但最终状态不对",
    "failed_to_recover_after_state_reset": "state reset 后没有恢复到正确工作流",
    "interruption_not_cleared_or_wrongly_ignored": "弹窗/通知没有被正确处理",
    "misread_delayed_transition_or_loading_state": "把 loading / frozen / skeleton 当成稳定界面",
    "looping_under_interruption": "在中断界面下反复执行同一动作",
    "looping_after_transition_perturbation": "在延迟/过渡扰动后进入循环",
    "looping_after_state_or_layout_shift": "状态/布局变化后进入循环",
    "state_or_layout_shift_confusion": "字体/主题/密度/时间格式变化导致理解偏差",
    "task_loop": "没有处理中断，但在任务本身流程里循环卡住",
    "task_progress_stalled": "流程推进停滞，未找到明确恢复策略",
    "unknown_eval": "评测结果缺失或 NaN",
}


PERTURBATION_FAMILY_CN = {
    "baseline": "Baseline",
    "state": "State",
    "action": "Action",
    "transition": "Transition",
}


LAUNCHER_HINTS = ("launcher", "nexuslauncher")


@dataclass
class RunAnalysis:
    task: str
    repeat_index: int
    profile_name: str
    profile_group: str
    goal: str
    success: float | None
    success_source: str
    return_code: int
    run_dir: str | None
    traj_output_path: str
    per_run_log_path: str
    reason: str
    reason_cn: str
    reason_family: str
    episode_length: int | None
    run_time: float | None
    last_action: str | None
    last_action_type: str | None
    last_goal_status: str | None
    same_action_suffix: int
    same_response_suffix: int
    overlay_present: bool
    overlay_matches: list[str]
    final_package: str | None
    final_ui_texts: list[str]
    final_ui_excerpt: str
    target_quote: str | None
    exception_summary: str | None
    perturbation_specific: bool


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_run_dir_from_log(log_path: Path) -> Path | None:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Wrote to (.+?run_[0-9T]+)", text)
    if match:
        return Path(match.group(1))
    return None


def _extract_texts(ui_elements: list[Any]) -> list[str]:
    texts: list[str] = []
    seen: set[str] = set()
    for element in ui_elements:
        for attr in ("text", "content_description", "hint_text"):
            value = getattr(element, attr, None)
            if value is None:
                continue
            value = str(value).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            texts.append(value)
    return texts


def _common_package(ui_elements: list[Any]) -> str | None:
    counts: collections.Counter[str] = collections.Counter()
    for element in ui_elements:
        package_name = getattr(element, "package_name", None)
        if package_name:
            counts[str(package_name)] += 1
    return counts.most_common(1)[0][0] if counts else None


def _clean_response_text(response: Any) -> str:
    if response is None:
        return ""
    text = str(response)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _suffix_repeat_count(values: list[str]) -> int:
    if not values:
        return 0
    last = values[-1]
    count = 0
    for value in reversed(values):
        if value == last:
            count += 1
        else:
            break
    return count


def _goal_target_quote(goal: str) -> str | None:
    matches = re.findall(r'"([^"]+)"', goal)
    return matches[0] if matches else None


def _tokenize_for_match(text: str) -> list[str]:
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return [token for token in tokens if token]


def _target_partially_visible(target_quote: str | None, final_ui_texts: list[str]) -> bool:
    if not target_quote:
        return False
    target_tokens = _tokenize_for_match(target_quote)
    if len(target_tokens) < 2:
        return False
    final_blob = " ".join(final_ui_texts).lower()
    matched = sum(1 for token in target_tokens if token in final_blob)
    return 0 < matched < len(target_tokens)


def _target_near_match(target_quote: str | None, final_ui_texts: list[str]) -> bool:
    if not target_quote:
        return False
    target_lower = target_quote.lower()
    for text in final_ui_texts:
        text_lower = text.lower()
        if text_lower == target_lower:
            return False
        if target_lower in text_lower or text_lower in target_lower:
            return True
    return False


def _action_signature(action: Any) -> str:
    if action is None:
        return "none"
    action_type = getattr(action, "action_type", None)
    if action_type == "click":
        return f"click:{getattr(action, 'x', None)}:{getattr(action, 'y', None)}"
    if action_type == "swipe":
        return f"swipe:{tuple(getattr(action, 'direction', None) or [])}"
    if action_type == "type":
        typed = getattr(action, "text", None) or ""
        return f"type:{typed[:40]}"
    if action_type == "status":
        return f"status:{getattr(action, 'goal_status', None)}"
    if action_type == "open_app":
        return f"open_app:{getattr(action, 'app_name', None)}"
    return str(action_type or "unknown")


def _exception_summary(exception_info: Any) -> str | None:
    if not exception_info or _is_nan(exception_info):
        return None
    lines = [line.strip() for line in str(exception_info).splitlines() if line.strip()]
    if not lines:
        return None
    for line in reversed(lines):
        if not line.startswith("^") and not line.startswith("File "):
            return line[:240]
    return lines[-1][:240]


def _classify_run(
    record: dict[str, Any],
    episode: dict[str, Any],
    run_dir: Path | None,
) -> RunAnalysis:
    profile_name = str(record["profile_name"])
    profile_group = PROFILE_GROUP.get(profile_name, "unknown")
    success = record.get("success")
    goal = str(episode.get("goal") or record["task"])
    target_quote = _goal_target_quote(goal)
    exception_info = episode.get("exception_info")
    exception_summary = _exception_summary(exception_info)

    episode_data = episode.get("episode_data")
    if episode_data is None or _is_nan(episode_data):
        reason = "runtime_exception_before_eval" if exception_summary else "unknown_eval"
        return RunAnalysis(
            task=str(record["task"]),
            repeat_index=int(record["repeat_index"]),
            profile_name=profile_name,
            profile_group=profile_group,
            goal=goal,
            success=success,
            success_source=str(record.get("success_source")),
            return_code=int(record.get("return_code", 0)),
            run_dir=str(run_dir) if run_dir else None,
            traj_output_path=str(record["traj_output_path"]),
            per_run_log_path=str(record["per_run_log_path"]),
            reason=reason,
            reason_cn=REASON_CN[reason],
            reason_family=REASON_FAMILY[reason],
            episode_length=None,
            run_time=None,
            last_action=None,
            last_action_type=None,
            last_goal_status=None,
            same_action_suffix=0,
            same_response_suffix=0,
            overlay_present=False,
            overlay_matches=[],
            final_package=None,
            final_ui_texts=[],
            final_ui_excerpt="",
            target_quote=target_quote,
            exception_summary=exception_summary,
            perturbation_specific=False,
        )

    actions = list(episode_data.get("action") or [])
    action_signatures = [_action_signature(action) for action in actions]
    responses = [_clean_response_text(response) for response in episode_data.get("action_response") or []]
    ui_steps = list(episode_data.get("ui_elements") or [])
    final_ui_elements = ui_steps[-1] if ui_steps else []
    final_ui_texts = _extract_texts(final_ui_elements)
    final_ui_excerpt = " || ".join(final_ui_texts[:10])
    final_package = _common_package(final_ui_elements)
    final_blob = " | ".join(final_ui_texts[:40]).lower()
    overlay_matches = [
        keyword
        for keyword in PROFILE_KEYWORDS.get(profile_name, [])
        if keyword in final_blob
    ]
    overlay_present = bool(overlay_matches)
    final_home = bool(final_package) and any(
        hint in final_package.lower() for hint in LAUNCHER_HINTS
    )
    last_action = actions[-1] if actions else None
    last_action_type = getattr(last_action, "action_type", None) if last_action else None
    last_goal_status = getattr(last_action, "goal_status", None) if last_action else None
    episode_length = episode.get("episode_length")
    if _is_nan(episode_length):
        episode_length = None
    run_time = episode.get("run_time")
    if _is_nan(run_time):
        run_time = None

    same_action_suffix = _suffix_repeat_count(action_signatures)
    same_response_suffix = _suffix_repeat_count(responses)
    target_partially_visible = _target_partially_visible(target_quote, final_ui_texts)
    target_near_match = _target_near_match(target_quote, final_ui_texts)

    if success == 1.0:
        reason = "success"
    elif success is None:
        reason = "unknown_eval"
    elif success == 0.5:
        reason = "partial_success"
    elif last_action_type == "status" and last_goal_status == "task_complete":
        if overlay_present:
            reason = "declared_done_but_overlay_or_popup_still_interfering"
        elif target_near_match or target_partially_visible:
            reason = "declared_done_but_exact_target_not_met"
        else:
            reason = "declared_done_but_wrong_end_state"
    elif profile_name == "state_reset_home" and final_home:
        reason = "failed_to_recover_after_state_reset"
    elif profile_name in ACTION_PROFILES and overlay_present:
        reason = "interruption_not_cleared_or_wrongly_ignored"
    elif profile_name in TRANSITION_PROFILES and overlay_present:
        reason = "misread_delayed_transition_or_loading_state"
    elif same_action_suffix >= 4 or same_response_suffix >= 3 or episode_length == 30:
        if profile_name in ACTION_PROFILES:
            reason = "looping_under_interruption"
        elif profile_name in TRANSITION_PROFILES:
            reason = "looping_after_transition_perturbation"
        elif profile_name in STATE_PROFILES:
            reason = "looping_after_state_or_layout_shift"
        else:
            reason = "task_loop"
    elif profile_name in STATE_PROFILES and profile_name != "state_reset_home":
        reason = "state_or_layout_shift_confusion"
    else:
        reason = "task_progress_stalled"

    reason_family = REASON_FAMILY[reason]
    perturbation_specific = reason_family in {
        "state_perturbation",
        "action_perturbation",
        "transition_perturbation",
    }

    return RunAnalysis(
        task=str(record["task"]),
        repeat_index=int(record["repeat_index"]),
        profile_name=profile_name,
        profile_group=profile_group,
        goal=goal,
        success=success,
        success_source=str(record.get("success_source")),
        return_code=int(record.get("return_code", 0)),
        run_dir=str(run_dir) if run_dir else None,
        traj_output_path=str(record["traj_output_path"]),
        per_run_log_path=str(record["per_run_log_path"]),
        reason=reason,
        reason_cn=REASON_CN[reason],
        reason_family=reason_family,
        episode_length=int(episode_length) if episode_length is not None else None,
        run_time=float(run_time) if run_time is not None else None,
        last_action=_action_signature(last_action) if last_action else None,
        last_action_type=str(last_action_type) if last_action_type else None,
        last_goal_status=str(last_goal_status) if last_goal_status else None,
        same_action_suffix=same_action_suffix,
        same_response_suffix=same_response_suffix,
        overlay_present=overlay_present,
        overlay_matches=overlay_matches,
        final_package=final_package,
        final_ui_texts=final_ui_texts[:20],
        final_ui_excerpt=final_ui_excerpt,
        target_quote=target_quote,
        exception_summary=exception_summary,
        perturbation_specific=perturbation_specific,
    )


def _summarize_group(runs: list[RunAnalysis], label: str) -> dict[str, Any]:
    successes = sum(1 for run in runs if run.success == 1.0)
    failures = sum(1 for run in runs if run.success == 0.0)
    partial_or_unknown = sum(1 for run in runs if run.success not in {0.0, 1.0})
    reason_counts = collections.Counter(
        run.reason_family for run in runs if run.success != 1.0
    )
    return {
        "group": label,
        "num_runs": len(runs),
        "num_successes": successes,
        "num_failures": failures,
        "num_partial_or_unknown": partial_or_unknown,
        "strict_success_rate": successes / len(runs) if runs else None,
        "top_failure_families": reason_counts.most_common(5),
    }


def _task_pattern(task_runs: list[RunAnalysis]) -> dict[str, Any]:
    task_runs = sorted(task_runs, key=lambda run: run.repeat_index)
    failed_runs = [run for run in task_runs if run.success != 1.0]
    failed_reason_families = sorted({run.reason_family for run in failed_runs})
    failed_reasons = sorted({run.reason for run in failed_runs})

    if not failed_runs:
        failure_pattern = "all_success"
    elif len(failed_reasons) == 1:
        failure_pattern = "same_reason"
    elif len(failed_reason_families) == 1:
        failure_pattern = "same_family_diff_reason"
    else:
        failure_pattern = "different_reasons"

    perturbation_specific_failures = sum(1 for run in failed_runs if run.perturbation_specific)
    task_intrinsic_failures = sum(
        1 for run in failed_runs if run.reason_family == "task_intrinsic_or_general"
    )
    exception_failures = sum(1 for run in failed_runs if run.reason_family == "exception")

    return {
        "task": task_runs[0].task,
        "goal": task_runs[0].goal,
        "num_successes": sum(1 for run in task_runs if run.success == 1.0),
        "num_failures": sum(1 for run in task_runs if run.success == 0.0),
        "num_partial_or_unknown": sum(1 for run in task_runs if run.success not in {0.0, 1.0}),
        "failure_pattern": failure_pattern,
        "failed_reasons": failed_reasons,
        "failed_reason_families": failed_reason_families,
        "perturbation_specific_failures": perturbation_specific_failures,
        "task_intrinsic_failures": task_intrinsic_failures,
        "exception_failures": exception_failures,
        "runs": [asdict(run) for run in task_runs],
    }


def _format_run_line(run: RunAnalysis) -> str:
    status = (
        "success"
        if run.success == 1.0
        else "partial/unknown"
        if run.success not in {0.0, 1.0}
        else "fail"
    )
    extras: list[str] = []
    if run.target_quote:
        extras.append(f"target=`{run.target_quote}`")
    if run.overlay_matches:
        extras.append("overlay=" + ", ".join(run.overlay_matches[:3]))
    if run.exception_summary:
        extras.append(f"exception=`{run.exception_summary}`")
    if run.episode_length is not None:
        extras.append(f"steps={run.episode_length}")
    if run.last_action:
        extras.append(f"last={run.last_action}")
    if run.final_ui_excerpt:
        extras.append(f"ui=`{run.final_ui_excerpt[:160]}`")
    return (
        f"- r{run.repeat_index} `{run.profile_name}` [{PERTURBATION_FAMILY_CN.get(run.profile_group, run.profile_group)}] "
        f"{status}: {run.reason_cn}."
        + (" " + "; ".join(extras) if extras else "")
    )


def _write_markdown_report(
    output_path: Path,
    session_dir: Path,
    run_analyses: list[RunAnalysis],
    task_summaries: list[dict[str, Any]],
) -> None:
    total_runs = len(run_analyses)
    total_tasks = len(task_summaries)
    strict_successes = sum(1 for run in run_analyses if run.success == 1.0)
    strict_failures = sum(1 for run in run_analyses if run.success == 0.0)
    partial_or_unknown = total_runs - strict_successes - strict_failures
    pattern_counts = collections.Counter(summary["failure_pattern"] for summary in task_summaries)

    by_group: dict[str, list[RunAnalysis]] = collections.defaultdict(list)
    for run in run_analyses:
        by_group[run.profile_group].append(run)

    lines: list[str] = []
    lines.append("# Random Perturbation Session Analysis")
    lines.append("")
    lines.append(f"- Session: `{session_dir}`")
    lines.append(f"- Unique tasks: `{total_tasks}`")
    lines.append(f"- Total runs: `{total_runs}`")
    lines.append(f"- Strict success / fail / partial-or-unknown: `{strict_successes} / {strict_failures} / {partial_or_unknown}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This session actually contains `116` unique tasks and `348` runs, not `114` tasks.")
    lines.append("- `summary.repeat_summary` only covers `343` runs because `5` runs have `success=None`; this report keeps them as `unknown/exception` instead of dropping them.")
    lines.append("- The 20 profiles in the session are `1 baseline (clean)` plus `19 perturbations` split into `State / Action / Transition`.")
    lines.append("")
    lines.append("## Group Summary")
    lines.append("")
    for group_name in ("baseline", "state", "action", "transition"):
        summary = _summarize_group(by_group.get(group_name, []), group_name)
        rate = summary["strict_success_rate"]
        rate_str = f"{rate:.3f}" if rate is not None else "n/a"
        lines.append(
            f"- `{group_name}`: runs={summary['num_runs']}, success={summary['num_successes']}, "
            f"fail={summary['num_failures']}, partial/unknown={summary['num_partial_or_unknown']}, "
            f"strict_success_rate={rate_str}"
        )
        if summary["top_failure_families"]:
            lines.append(
                "  top failure families: "
                + ", ".join(f"{name} ({count})" for name, count in summary["top_failure_families"])
            )
    lines.append("")
    lines.append("## Task-Level Pattern Counts")
    lines.append("")
    for key in ("all_success", "same_reason", "same_family_diff_reason", "different_reasons"):
        lines.append(f"- `{key}`: {pattern_counts.get(key, 0)} tasks")
    lines.append("")
    lines.append("## Per-Task Analysis")
    lines.append("")

    for summary in task_summaries:
        pattern_label = {
            "all_success": "3 次都成功",
            "same_reason": "失败原因基本一致",
            "same_family_diff_reason": "失败属于同一大类，但细节略有不同",
            "different_reasons": "失败原因明显不同",
        }[summary["failure_pattern"]]
        lines.append(f"### {summary['task']}")
        lines.append("")
        lines.append(f"- Goal: {summary['goal']}")
        lines.append(
            f"- Outcome: success={summary['num_successes']}, fail={summary['num_failures']}, "
            f"partial/unknown={summary['num_partial_or_unknown']}"
        )
        lines.append(f"- Pattern: {pattern_label}")
        lines.append(
            f"- Failure mix: perturbation-specific={summary['perturbation_specific_failures']}, "
            f"task-intrinsic/general={summary['task_intrinsic_failures']}, "
            f"exception={summary['exception_failures']}"
        )
        for run_dict in summary["runs"]:
            lines.append(_format_run_line(RunAnalysis(**run_dict)))
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--session-dir",
        type=Path,
        default=SCRIPT_DIR / "random_perturb_runs" / "session_2026-04-14_21-20-33",
        help="Path to a random_perturb_runs session directory.",
    )
    args = parser.parse_args()

    session_dir = args.session_dir.expanduser().resolve()
    summary_path = session_dir / "summary.json"
    summary = _read_json(summary_path)

    run_analyses: list[RunAnalysis] = []
    for record in summary["results"]:
        log_path = Path(record["per_run_log_path"])
        run_dir = _extract_run_dir_from_log(log_path)
        episode = {}
        if run_dir is not None:
            pkl_path = run_dir / f"{record['task']}_0.pkl.gz"
            with gzip.open(pkl_path, "rb") as file_obj:
                task_episodes = pickle.load(file_obj)
            episode = task_episodes[0]
        run_analyses.append(_classify_run(record, episode, run_dir))

    by_task: dict[str, list[RunAnalysis]] = collections.defaultdict(list)
    for run in run_analyses:
        by_task[run.task].append(run)

    task_summaries = [
        _task_pattern(task_runs)
        for _, task_runs in sorted(by_task.items(), key=lambda item: item[0].lower())
    ]

    analysis_dir = session_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    runs_json_path = analysis_dir / "run_analysis.json"
    tasks_json_path = analysis_dir / "task_analysis.json"
    report_md_path = analysis_dir / "analysis_report.md"

    runs_json_path.write_text(
        json.dumps([asdict(run) for run in run_analyses], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tasks_json_path.write_text(
        json.dumps(task_summaries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_markdown_report(report_md_path, session_dir, run_analyses, task_summaries)

    print(f"Wrote {runs_json_path}")
    print(f"Wrote {tasks_json_path}")
    print(f"Wrote {report_md_path}")


if __name__ == "__main__":
    main()
