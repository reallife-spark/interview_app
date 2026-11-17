#!/usr/bin/env bash
# Public Streamlit smoke: follow the anonymous auth bootstrap, not just the
# first-hop 303. A private app fails at the shell/iframe or browser title check.
set -euo pipefail

URL="${PUBLIC_APP_URL:-https://interviewap-nbsnftcgrwj7yjcm2h658m.streamlit.app/}"
USER_AGENT="${PUBLIC_APP_USER_AGENT:-Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/150 Safari/537.36}"
CHROMIUM="${CHROMIUM_BIN:-chromium}"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
jar="$tmpdir/cookies.txt"
body="$tmpdir/app.html"

final=$(curl -sS -L --max-redirs 10 --max-time 30 \
  -c "$jar" -b "$jar" -A "$USER_AGENT" \
  -o "$body" -w '%{http_code} %{url_effective} %{num_redirects}' "$URL")
read -r code effective redirects <<<"$final"

printf 'final_code=%s\n' "$code"
printf 'final_url=%s\n' "$effective"
printf 'redirects=%s\n' "$redirects"

fail=0
[[ "$code" == "200" ]] || fail=1
[[ "$effective" == "$URL" ]] || fail=1
grep -q 'streamlitApp' "$body" || fail=1

if ! command -v "$CHROMIUM" >/dev/null 2>&1; then
  echo "chromium is required for the public-app title check" >&2
  exit 2
fi

title=$(timeout 70 "$CHROMIUM" --headless=new --no-sandbox --disable-gpu \
  --disable-dev-shm-usage --incognito --virtual-time-budget=8000 \
  --dump-dom "$URL" 2>/dev/null \
  | grep -o '<title>[^<]*' | head -1 | sed 's/<title>//' || true)
printf 'browser_title=%s\n' "${title:-<missing>}"
[[ "$title" == Interview\ Practice\ Coach* ]] || fail=1

if [[ "$fail" -ne 0 ]]; then
  echo "public_app=failed" >&2
  exit 1
fi

echo "public_app=ok"
