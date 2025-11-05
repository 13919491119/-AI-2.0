#!/usr/bin/env bash
# One-shot script to execute canary deploy when kubeconfig is provided as KUBE_CONFIG_DATA (base64).
# Usage (recommended on trusted host):
#   export KUBE_CONFIG_DATA="$(cat /path/to/kubeconfig | base64 -w0)"
#   export AUTO_CONFIRM=true  # to allow real deploy (otherwise only dry-run)
#   ./tools/execute_canary.sh --artifact artifacts --namespace canary --metrics-endpoint http://canary-service.metrics.local/metrics

set -euo pipefail

ARTIFACT_DIR="artifacts"
NAMESPACE="canary"
METRICS_ENDPOINT=""
DRY_RUN=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --artifact) ARTIFACT_DIR=$2; shift 2;;
    --namespace) NAMESPACE=$2; shift 2;;
    --metrics-endpoint) METRICS_ENDPOINT=$2; shift 2;;
    --dry-run=*) DRY_RUN=${1#*=}; shift;;
    --dry-run) DRY_RUN=$2; shift 2;;
    -h|--help) echo "Usage: $0 --artifact <dir> --namespace <ns> --metrics-endpoint <url> [--dry-run=(true|false)]"; exit 0;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

LOGDIR="logs"
mkdir -p "$LOGDIR"
AUDIT_LOG="$LOGDIR/autonomy_audit.log"
CANARY_LOG="$LOGDIR/autonomy_canary_run.log"

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - execute_canary.sh start" | tee -a "$AUDIT_LOG" "$CANARY_LOG"

if [[ -z "${KUBE_CONFIG_DATA:-}" ]]; then
  echo "KUBE_CONFIG_DATA not found in environment. This script requires base64 kubeconfig in KUBE_CONFIG_DATA." | tee -a "$AUDIT_LOG" "$CANARY_LOG"
  echo "Exiting without changes." | tee -a "$AUDIT_LOG" "$CANARY_LOG"
  exit 2
fi

# prepare temporary kubeconfig
TMPDIR=$(mktemp -d /tmp/xuanji_kube.XXXX)
trap 'rm -rf "$TMPDIR"' EXIT

echo "$KUBE_CONFIG_DATA" | base64 -d > "$TMPDIR/config"
export KUBECONFIG="$TMPDIR/config"

echo "Wrote temporary kubeconfig to $TMPDIR/config" | tee -a "$AUDIT_LOG" "$CANARY_LOG"

# Dry-run by default unless DRY_RUN=false or AUTO_CONFIRM=true
if [[ "$DRY_RUN" == "true" ]]; then
  echo "Running deploy_canary.sh in dry-run mode" | tee -a "$AUDIT_LOG" "$CANARY_LOG"
  ./tools/deploy_canary.sh --artifact "$ARTIFACT_DIR" --namespace "$NAMESPACE" --dry-run=true 2>&1 | tee -a "$CANARY_LOG"
  echo "Dry-run complete. To perform real deploy, re-run with --dry-run=false and set AUTO_CONFIRM=true in environment." | tee -a "$AUDIT_LOG" "$CANARY_LOG"
  exit 0
fi

if [[ "${AUTO_CONFIRM:-false}" != "true" ]]; then
  echo "AUTO_CONFIRM not set to true; refusing to perform real deploy. Set AUTO_CONFIRM=true to allow." | tee -a "$AUDIT_LOG" "$CANARY_LOG"
  exit 3
fi

# real deploy path
echo "AUTO_CONFIRM=true and DRY_RUN=false - performing real canary deploy" | tee -a "$AUDIT_LOG" "$CANARY_LOG"
./tools/deploy_canary.sh --artifact "$ARTIFACT_DIR" --namespace "$NAMESPACE" --dry-run=false 2>&1 | tee -a "$CANARY_LOG"

# optionally start rollback monitor in background if metrics endpoint given
if [[ -n "$METRICS_ENDPOINT" ]]; then
  echo "Starting auto_rollback.py against $METRICS_ENDPOINT" | tee -a "$AUDIT_LOG" "$CANARY_LOG"
  nohup python3 tools/auto_rollback.py --canary-endpoint "$METRICS_ENDPOINT" --threshold-file tools/rollback_thresholds.json --interval 30 >>"$CANARY_LOG" 2>&1 &
  echo "Started auto_rollback.py (background). PID recorded in $CANARY_LOG" | tee -a "$AUDIT_LOG" "$CANARY_LOG"
fi

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - execute_canary.sh end" | tee -a "$AUDIT_LOG" "$CANARY_LOG"

# Note: temporary kubeconfig will be removed on exit by trap; if you wish to keep it, copy it elsewhere before exit.
