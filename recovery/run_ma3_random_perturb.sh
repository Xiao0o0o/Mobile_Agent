#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

current_time=$(date +"%Y-%m-%d_%H-%M-%S")

SUITE_FAMILY="${SUITE_FAMILY:-android_world}"
AGENT_NAME="${AGENT_NAME:-gui_owl}"
MODEL="${MODEL:-gui_owl_7b}"
API_KEY="${API_KEY:-sk-local}"
BASE_URL="${BASE_URL:-http://127.0.0.1:4243/v1}"
GUIOWL_VARIANT="${GUIOWL_VARIANT:-7b}"
GUIOWL_TEMPERATURE="${GUIOWL_TEMPERATURE:-0.1}"
TASKS="${TASKS:-}"
TASKS_FILE="${TASKS_FILE:-}"
REPEATS_PER_TASK="${REPEATS_PER_TASK:-1}"
SAMPLING_SEED="${SAMPLING_SEED:-20260427}"
GRPC_PORT="${GRPC_PORT:-8554}"
CONSOLE_PORT="${CONSOLE_PORT:-5554}"
SESSION_DIR="${SESSION_DIR:-$SCRIPT_DIR/random_perturb_runs/session_$current_time}"

variant_key=$(printf '%s %s' "$GUIOWL_VARIANT" "$MODEL" | tr '[:upper:]' '[:lower:]')
GUIOWL_COORDINATE_FORMAT="${GUIOWL_COORDINATE_FORMAT:-}"
if [ -z "$GUIOWL_COORDINATE_FORMAT" ]; then
  case "$variant_key" in
    *1.5*|*1_5*)
      GUIOWL_COORDINATE_FORMAT="qwen-vl"
      ;;
    *)
      GUIOWL_COORDINATE_FORMAT="abs_resized"
      ;;
  esac
fi

export GUIOWL_MIN_PIXELS="${GUIOWL_MIN_PIXELS:-3136}"
export GUIOWL_MAX_PIXELS="${GUIOWL_MAX_PIXELS:-2592000}"

PROFILE_NAMES="${PROFILE_NAMES:-font_size_large,font_size_small,ui_theme_dark,display_size_dpi_compact,display_size_dpi_zoomed_out,orientation_landscape,execution_delay_loading,execution_delay_frozen,partial_loading_skeleton,app_hang_restart_required,state_reset_home,bottom_sheet_consent,popup_permission,popup_security,interstitial_ad,ad_trial_offer,rate_dialog,update_system,update_app_sheet,notification_message,notification_delivery,locale_date_format_us12,locale_date_format_eu24,action_delay_realistic,action_drop_random}"

FONT_SIZE_LARGE_SCALE="${FONT_SIZE_LARGE_SCALE:-1.35}"
FONT_SIZE_SMALL_SCALE="${FONT_SIZE_SMALL_SCALE:-0.82}"
DISPLAY_COMPACT_DENSITY_SCALE="${DISPLAY_COMPACT_DENSITY_SCALE:-0.85}"
DISPLAY_COMPACT_SIZE_SCALE="${DISPLAY_COMPACT_SIZE_SCALE:-0.94}"
DISPLAY_ZOOMED_OUT_DENSITY_SCALE="${DISPLAY_ZOOMED_OUT_DENSITY_SCALE:-0.76}"
DISPLAY_ZOOMED_OUT_SIZE_SCALE="${DISPLAY_ZOOMED_OUT_SIZE_SCALE:-0.88}"
ORIENTATION_PROFILE_SEQUENCE="${ORIENTATION_PROFILE_SEQUENCE:-landscape}"
APP_HANG_TRIGGER_STEPS="${APP_HANG_TRIGGER_STEPS:-2}"
ACTION_DELAY_PROBABILITY="${ACTION_DELAY_PROBABILITY:-0.15}"
ACTION_DELAY_SECONDS="${ACTION_DELAY_SECONDS:-1.5}"
ACTION_DELAY_SEED="${ACTION_DELAY_SEED:-0}"
ACTION_DROP_PROBABILITY="${ACTION_DROP_PROBABILITY:-0.08}"
ACTION_DROP_SEED="${ACTION_DROP_SEED:-0}"
DOWNSTREAM_PRE_ACTION_ENABLE="${DOWNSTREAM_PRE_ACTION_ENABLE:-True}"
DOWNSTREAM_PRE_ACTION_LOG_ENABLE="${DOWNSTREAM_PRE_ACTION_LOG_ENABLE:-True}"
DOWNSTREAM_PRE_ACTION_USE_RECOVERY_PROMPT="${DOWNSTREAM_PRE_ACTION_USE_RECOVERY_PROMPT:-True}"
DOWNSTREAM_PRE_ACTION_WAIT_SECONDS="${DOWNSTREAM_PRE_ACTION_WAIT_SECONDS:-2.0}"
DOWNSTREAM_RECOVERY_MAX_STEPS="${DOWNSTREAM_RECOVERY_MAX_STEPS:-3}"
DOWNSTREAM_HARD_STUCK_WINDOW="${DOWNSTREAM_HARD_STUCK_WINDOW:-3}"
EPISODE_STEP_BUDGET_MULTIPLIER="${EPISODE_STEP_BUDGET_MULTIPLIER:-20.0}"


set -- \
  python run_random_perturb_batch.py \
  --suite-family="$SUITE_FAMILY" \
  --repeats-per-task="$REPEATS_PER_TASK" \
  --sampling-seed="$SAMPLING_SEED" \
  --session-dir="$SESSION_DIR" \
  --agent="$AGENT_NAME" \
  --model="$MODEL" \
  --api-key="$API_KEY" \
  --base-url="$BASE_URL" \
  --guiowl-coordinate-format="$GUIOWL_COORDINATE_FORMAT" \
  --guiowl-temperature="$GUIOWL_TEMPERATURE" \
  --grpc-port="$GRPC_PORT" \
  --console-port="$CONSOLE_PORT" \
  --profiles="$PROFILE_NAMES" \
  --font-size-large-scale="$FONT_SIZE_LARGE_SCALE" \
  --font-size-small-scale="$FONT_SIZE_SMALL_SCALE" \
  --display-compact-density-scale="$DISPLAY_COMPACT_DENSITY_SCALE" \
  --display-compact-size-scale="$DISPLAY_COMPACT_SIZE_SCALE" \
  --display-zoomed-out-density-scale="$DISPLAY_ZOOMED_OUT_DENSITY_SCALE" \
  --display-zoomed-out-size-scale="$DISPLAY_ZOOMED_OUT_SIZE_SCALE" \
  --orientation-profile-sequence="$ORIENTATION_PROFILE_SEQUENCE" \
  --app-hang-trigger-steps="$APP_HANG_TRIGGER_STEPS" \
  --action-delay-probability="$ACTION_DELAY_PROBABILITY" \
  --action-delay-seconds="$ACTION_DELAY_SECONDS" \
  --action-delay-seed="$ACTION_DELAY_SEED" \
  --action-drop-probability="$ACTION_DROP_PROBABILITY" \
  --action-drop-seed="$ACTION_DROP_SEED" \
  --downstream-pre-action-enable="$DOWNSTREAM_PRE_ACTION_ENABLE" \
  --downstream-pre-action-log-enable="$DOWNSTREAM_PRE_ACTION_LOG_ENABLE" \
  --downstream-pre-action-use-recovery-prompt="$DOWNSTREAM_PRE_ACTION_USE_RECOVERY_PROMPT" \
  --downstream-pre-action-wait-seconds="$DOWNSTREAM_PRE_ACTION_WAIT_SECONDS" \
  --downstream-recovery-max-steps="$DOWNSTREAM_RECOVERY_MAX_STEPS" \
  --downstream-hard-stuck-window="$DOWNSTREAM_HARD_STUCK_WINDOW" \
  --episode-step-budget-multiplier="$EPISODE_STEP_BUDGET_MULTIPLIER" \
  --disable-clean

if [ -n "$TASKS_FILE" ]; then
  set -- "$@" --tasks-file="$TASKS_FILE"
fi

if [ -n "$TASKS" ]; then
  set -- "$@" --tasks="$TASKS"
fi

{
  "$@"
  printf '\n[END_TIME] %s\n' "$(date +"%Y-%m-%d %H:%M:%S %Z")"
}
