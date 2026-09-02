#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install_openclaw.sh [options]

Options:
  --workspace PATH  Install into this OpenClaw workspace.
  --profile NAME    Read workspace from an OpenClaw profile.
  --dev             Use the OpenClaw development profile.
  --with-creator    Also install the development-only skill creator.
  --force           Back up and replace conflicting FraudGuard files.
  -h, --help        Show this help.
EOF
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"
workspace=""
profile=""
use_dev=0
force=0
with_creator=0

while (($#)); do
  case "$1" in
    --workspace)
      [[ $# -ge 2 ]] || { echo "--workspace requires a path" >&2; exit 2; }
      workspace="$2"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a name" >&2; exit 2; }
      profile="$2"
      shift 2
      ;;
    --dev)
      use_dev=1
      shift
      ;;
    --force)
      force=1
      shift
      ;;
    --with-creator)
      with_creator=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$profile" && $use_dev -eq 1 ]]; then
  echo "Choose either --profile or --dev, not both" >&2
  exit 2
fi

openclaw_args=()
if [[ -n "$profile" ]]; then
  openclaw_args+=(--profile "$profile")
elif [[ $use_dev -eq 1 ]]; then
  openclaw_args+=(--dev)
fi

if [[ -z "$workspace" ]]; then
  command -v openclaw >/dev/null || {
    echo "OpenClaw CLI not found; pass --workspace explicitly after installing OpenClaw" >&2
    exit 1
  }
  workspace="$(openclaw "${openclaw_args[@]}" config get agents.defaults.workspace)"
  workspace="${workspace%\"}"
  workspace="${workspace#\"}"
fi

if [[ -z "$workspace" || "$workspace" != /* ]]; then
  echo "OpenClaw workspace must be a non-empty absolute path: $workspace" >&2
  exit 1
fi

skills=(fraud-detection safety-payment realtime-intervention)
if [[ $with_creator -eq 1 ]]; then
  skills+=(skill-creator)
fi
for skill in "${skills[@]}"; do
  [[ -f "${repo_root}/skills/${skill}/SKILL.md" ]] || {
    echo "Missing source skill: skills/${skill}/SKILL.md" >&2
    exit 1
  }
done
[[ -f "${repo_root}/scripts/fraudguard_agent_cli.py" ]] || {
  echo "Missing CLI source: scripts/fraudguard_agent_cli.py" >&2
  exit 1
}

backup_root="${workspace}/.fraudguard-backups/$(date -u +%Y%m%dT%H%M%SZ)"
changed=0

install_directory() {
  local source_path="$1"
  local target_path="$2"
  local backup_path="$3"
  if [[ -e "$target_path" ]]; then
    if diff -qr "$source_path" "$target_path" >/dev/null; then
      echo "unchanged: $target_path"
      return
    fi
    if [[ $force -ne 1 ]]; then
      echo "Conflict: $target_path already exists; rerun with --force to back it up" >&2
      exit 1
    fi
    mkdir -p "$(dirname -- "$backup_path")"
    mv "$target_path" "$backup_path"
    echo "backup: $target_path -> $backup_path"
  fi
  mkdir -p "$(dirname -- "$target_path")"
  cp -a "$source_path" "$target_path"
  echo "installed: $target_path"
  changed=1
}

install_file() {
  local source_path="$1"
  local target_path="$2"
  local backup_path="$3"
  if [[ -e "$target_path" ]]; then
    if cmp -s "$source_path" "$target_path"; then
      chmod 700 "$target_path"
      echo "unchanged: $target_path"
      return
    fi
    if [[ $force -ne 1 ]]; then
      echo "Conflict: $target_path already exists; rerun with --force to back it up" >&2
      exit 1
    fi
    mkdir -p "$(dirname -- "$backup_path")"
    mv "$target_path" "$backup_path"
    echo "backup: $target_path -> $backup_path"
  fi
  mkdir -p "$(dirname -- "$target_path")"
  cp "$source_path" "$target_path"
  chmod 700 "$target_path"
  echo "installed: $target_path"
  changed=1
}

for skill in "${skills[@]}"; do
  install_directory \
    "${repo_root}/skills/${skill}" \
    "${workspace}/skills/${skill}" \
    "${backup_root}/skills/${skill}"
done
install_file \
  "${repo_root}/scripts/fraudguard_agent_cli.py" \
  "${workspace}/tools/fraudguard-agent" \
  "${backup_root}/tools/fraudguard-agent"

echo
echo "FraudGuard OpenClaw files are ready in: $workspace"
if [[ $changed -eq 0 ]]; then
  echo "No files changed. Installation is already current."
fi
if [[ ${#openclaw_args[@]} -gt 0 ]]; then
  echo "Validate with: openclaw ${openclaw_args[*]} skills info fraud-detection"
else
  echo "Validate with: openclaw skills info fraud-detection"
fi
echo "Test bridge:  ${workspace}/tools/fraudguard-agent health"
echo "Open a new OpenClaw session after installation so the skill snapshot refreshes."
