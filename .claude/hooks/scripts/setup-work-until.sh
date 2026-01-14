#!/bin/bash

# Work-Until Loop Setup Script
# Creates state file for work-until loop

set -euo pipefail


# Parse arguments
PROMPT_PARTS=()
COMPLETION_PHRASE=""
MAX_ITERATIONS=0

show_help() {
  cat << 'HELP_EOF'
Work-Until Loop - Iterative task completion loop

USAGE:
  /work-until PROMPT [OPTIONS]

ARGUMENTS:
  PROMPT    The task to work on (resent each iteration)

OPTIONS:
  --completion-phrase <text>  Phrase to signal completion (use quotes for multi-word)
  --max-iterations <n>        Maximum iterations before auto-stop (default: 0 = unlimited)
  -h, --help                  Show this help message

DESCRIPTION:
  Starts a work-until loop in your CURRENT session. The stop hook prevents
  exit and keeps you working on the same PROMPT until:
  1. You output <complete>PHRASE</complete> (phrase must be TRUE), OR
  2. Max iterations reached (if set)

  Between iterations, the normal stop hook checks run (memory, session context,
  tests, etc.) so work is properly tracked.

EXAMPLES:
  /work-until Fix all failing tests --completion-phrase "All tests pass"
  /work-until Implement auth feature --completion-phrase "Feature complete" --max-iterations 10
  /work-until Refactor the API layer --max-iterations 5

STOPPING:
  Output: <complete>Your phrase here</complete>
  The phrase must be TRUE - do not lie to exit the loop.

MONITORING:
  cat .meridian/.loop-state
HELP_EOF
  exit 0
}

# Parse options and collect prompt parts
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      ;;
    --max-iterations)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --max-iterations requires a number" >&2
        exit 1
      fi
      if ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "Error: --max-iterations must be a positive integer, got: $2" >&2
        exit 1
      fi
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --completion-phrase)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --completion-phrase requires a text argument" >&2
        exit 1
      fi
      COMPLETION_PHRASE="$2"
      shift 2
      ;;
    *)
      # Collect as prompt parts
      PROMPT_PARTS+=("$1")
      shift
      ;;
  esac
done

# Join prompt parts
PROMPT="${PROMPT_PARTS[*]}"

# Validate prompt
if [[ -z "$PROMPT" ]]; then
  echo "Error: Prompt is required" >&2
  echo "" >&2
  echo "Usage: /work-until PROMPT [--completion-phrase TEXT] [--max-iterations N]" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  /work-until Fix all failing tests --completion-phrase \"All tests pass\"" >&2
  echo "  /work-until Implement auth feature --max-iterations 10" >&2
  exit 1
fi

# Create state file
mkdir -p .meridian

# Write state file with prompt
cat > .meridian/.loop-state <<EOF
active: true
iteration: 1
max_iterations: $MAX_ITERATIONS
completion_phrase: "$COMPLETION_PHRASE"
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---
$PROMPT
EOF

# Output status
echo "🔄 Work-until loop activated!"
echo ""
echo "Task: $PROMPT"
if [[ -n "$COMPLETION_PHRASE" ]]; then
  echo "Completion phrase: $COMPLETION_PHRASE"
  echo "To exit, output: <complete>$COMPLETION_PHRASE</complete>"
else
  echo "Completion phrase: not set"
fi
if [[ $MAX_ITERATIONS -gt 0 ]]; then
  echo "Max iterations: $MAX_ITERATIONS"
else
  echo "Max iterations: unlimited"
fi
echo ""
if [[ -n "$COMPLETION_PHRASE" ]]; then
  echo "The stop hook will keep you working until you output the completion phrase (must be TRUE)."
elif [[ $MAX_ITERATIONS -gt 0 ]]; then
  echo "The stop hook will keep you working for $MAX_ITERATIONS iterations."
else
  echo "WARNING: No completion phrase or max iterations set - loop runs forever!"
fi
