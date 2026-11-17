#!/usr/bin/env bash
# Read-only public-gateway smoke. Requires LOCAL_API_KEY; never prints it.
set -euo pipefail

BASE="${LOCAL_BASE_URL:-https://real-life.dev/v1}"
HEALTH_URL="${GATEWAY_HEALTH_URL:-https://real-life.dev/healthz}"
TOKEN="${LOCAL_API_KEY:-}"

if [[ -z "$TOKEN" ]]; then
  echo "LOCAL_API_KEY is required" >&2
  exit 2
fi

status() {
  curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "$@" 2>/dev/null || true
}

health=$(status "$HEALTH_URL")
noauth=$(status "$BASE/models")
auth=$(status -H "Authorization: Bearer $TOKEN" "$BASE/models")
root="${BASE%/v1}"
api=$(status "$root/api/tags")
post_models=$(status -X POST -H "Authorization: Bearer $TOKEN" "$BASE/models")
get_chat=$(status -H "Authorization: Bearer $TOKEN" "$BASE/chat/completions")
direct=$(status --max-time 3 "http://152.53.196.118:11434/api/tags")

printf 'health=%s\n' "$health"
printf 'models_noauth=%s\n' "$noauth"
printf 'models_auth=%s\n' "$auth"
printf 'api_tags=%s\n' "$api"
printf 'post_models=%s\n' "$post_models"
printf 'get_chat=%s\n' "$get_chat"
printf 'direct_11434=%s\n' "$direct"

fail=0
[[ "$health" == "200" ]] || fail=1
[[ "$noauth" == "401" ]] || fail=1
[[ "$auth" == "200" ]] || fail=1
[[ "$api" != "200" ]] || fail=1
[[ "$post_models" == "403" || "$post_models" == "405" ]] || fail=1
[[ "$get_chat" == "403" || "$get_chat" == "405" ]] || fail=1
[[ "$direct" != "200" ]] || fail=1

exit "$fail"
