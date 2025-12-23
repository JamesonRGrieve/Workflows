#!/bin/bash
# Shared script for determining parallel worker count based on cgroup CPU limits
# Usage: source this script, then call: WORKERS=$(determine_workers "$PARALLEL_WORKERS_INPUT" "$RUNS_ON_INPUT")
#
# Arguments:
#   $1 - parallel_workers input value (empty string, "auto", or a number)
#   $2 - runs_on input value (JSON array string like '["self-hosted", "multithreaded"]')
#
# Returns: Number of workers to use (prints to stdout)

cgroup_auto_workers() {
  local n=""

  # cgroup v2: /sys/fs/cgroup/cpu.max => "<quota> <period>" or "max <period>"
  if [ -f /sys/fs/cgroup/cpu.max ]; then
    local quota period
    quota="$(awk '{print $1}' /sys/fs/cgroup/cpu.max)"
    period="$(awk '{print $2}' /sys/fs/cgroup/cpu.max)"
    if [ -n "$quota" ] && [ -n "$period" ] && [ "$quota" != "max" ] && [ "$period" != "0" ]; then
      n="$(awk -v q="$quota" -v p="$period" 'BEGIN{print int((q+p-1)/p)}')"
    fi
  fi

  # cgroup v1: cpu.cfs_quota_us / cpu.cfs_period_us
  if [ -z "$n" ] && [ -f /sys/fs/cgroup/cpu/cpu.cfs_quota_us ] && [ -f /sys/fs/cgroup/cpu/cpu.cfs_period_us ]; then
    local quota period
    quota="$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)"
    period="$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)"
    if [ "$quota" -gt 0 ] && [ "$period" -gt 0 ]; then
      n="$(awk -v q="$quota" -v p="$period" 'BEGIN{print int((q+p-1)/p)}')"
    fi
  fi

  # cpuset fallback (v2: /sys/fs/cgroup/cpuset.cpus ; v1: /sys/fs/cgroup/cpuset/cpuset.cpus)
  if [ -z "$n" ]; then
    local f=""
    if [ -f /sys/fs/cgroup/cpuset.cpus ]; then
      f="/sys/fs/cgroup/cpuset.cpus"
    elif [ -f /sys/fs/cgroup/cpuset/cpuset.cpus ]; then
      f="/sys/fs/cgroup/cpuset/cpuset.cpus"
    fi

    if [ -n "$f" ]; then
      local spec
      spec="$(cat "$f" | tr -d '[:space:]')"
      if [ -n "$spec" ]; then
        local count=0
        IFS=',' read -r -a parts <<< "$spec"
        for p in "${parts[@]}"; do
          if [[ "$p" == *-* ]]; then
            local a="${p%%-*}"
            local b="${p##*-}"
            if [[ "$a" =~ ^[0-9]+$ && "$b" =~ ^[0-9]+$ && "$b" -ge "$a" ]]; then
              count=$((count + b - a + 1))
            fi
          elif [[ "$p" =~ ^[0-9]+$ ]]; then
            count=$((count + 1))
          fi
        done
        if [ "$count" -gt 0 ]; then
          n="$count"
        fi
      fi
    fi
  fi

  if [ -z "$n" ] || [ "$n" -lt 1 ] 2>/dev/null; then
    n="1"
  fi

  echo "$n"
}

determine_workers() {
  local parallel_workers_input="$1"
  local runs_on_input="$2"
  local workers=""

  if [ -z "$parallel_workers_input" ]; then
    # Default based on runner type
    if echo "$runs_on_input" | grep -q "multithreaded"; then
      workers="6"
    else
      workers="1"
    fi
  elif [ "$parallel_workers_input" = "auto" ]; then
    workers="$(cgroup_auto_workers)"
  else
    # Use the provided number directly
    workers="$parallel_workers_input"
  fi

  echo "$workers"
}

# If script is executed directly (not sourced), run determine_workers with args
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  determine_workers "$1" "$2"
fi
