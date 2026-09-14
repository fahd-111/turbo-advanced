#!/bin/sh
# Blocks Claude from committing or pushing. The engineer does this by hand after /review.
cmd=$(cat | jq -r '.tool_input.command // empty')
case "$cmd" in
  *"git commit"*|*"git push"*|*"git merge"*|*"git rebase"*)
    echo "Blocked: commits, pushes, merges and rebases are done by the engineer after /review." >&2
    exit 2 ;;
esac
exit 0
