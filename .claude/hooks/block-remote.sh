#!/bin/sh
# Claude never connects to a client server. The engineer runs all remote commands by hand.
cmd=$(cat | jq -r '.tool_input.command // empty')
case "$cmd" in
  ssh\ *|*\ ssh\ *|scp\ *|*\ scp\ *|sftp\ *|*\ sftp\ *|rsync\ *|*\ rsync\ *)
    echo "Blocked: Claude does not connect to client servers. Run this yourself in your terminal." >&2
    exit 2 ;;
esac
exit 0
