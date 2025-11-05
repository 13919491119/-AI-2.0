#!/usr/bin/env bash
# Simple rollback helper for canary deployments.
# Usage: ./tools/rollback_helper.sh --deployment <name> --namespace <ns> [--confirm] [--dry-run=(true|false)]

set -euo pipefail

DEPLOYMENT=""
NAMESPACE="canary"
CONFIRM=false
DRY_RUN=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --deployment) DEPLOYMENT=$2; shift 2;;
    --namespace) NAMESPACE=$2; shift 2;;
    --confirm) CONFIRM=true; shift 1;;
    --dry-run=*) DRY_RUN=${1#*=}; shift;;
    --dry-run) DRY_RUN=$2; shift 2;;
    -h|--help) echo "Usage: $0 --deployment <name> --namespace <ns> [--confirm] [--dry-run=(true|false)]"; exit 0;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

if [[ -z "$DEPLOYMENT" ]]; then
  echo "--deployment required" >&2
  exit 2
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "DRY RUN: would run 'kubectl -n $NAMESPACE rollout undo deployment/$DEPLOYMENT'"
  echo "To perform rollback pass --dry-run=false and --confirm"
  exit 0
fi

if [[ "$CONFIRM" != "true" ]]; then
  echo "Refusing to perform rollback without --confirm flag" >&2
  exit 3
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl not found on PATH" >&2
  exit 4
fi

echo "Performing rollback of deployment/$DEPLOYMENT in namespace $NAMESPACE"
kubectl -n "$NAMESPACE" rollout undo deployment/"$DEPLOYMENT"

echo "Rollback triggered. Consider checking status: kubectl -n $NAMESPACE rollout status deployment/$DEPLOYMENT"
