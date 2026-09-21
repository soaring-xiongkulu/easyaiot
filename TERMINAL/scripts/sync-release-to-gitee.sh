#!/usr/bin/env bash
#
# Sync GitHub Release assets to the Gitee mirror's Releases.
#
# Downloads assets from a GitHub Release and (re)uploads them as attachments to
# the matching Gitee Release. Idempotent: existing Gitee releases are reused and
# already-attached files with the same name are skipped.
#
# Usage:
#   GITEE_TOKEN=xxxx ./scripts/sync-release-to-gitee.sh v1.2.1 [v1.2.0 ...]
#   GITEE_TOKEN=xxxx ./scripts/sync-release-to-gitee.sh --all
#
# Requirements: gh (logged in), curl, python.
#
set -euo pipefail

GH_REPO="${GH_REPO:-ys-ll/uniterm}"
GITEE_REPO="${GITEE_REPO:-ys-l/uniterm}"
GITEE_API="${GITEE_API:-https://gitee.com/api/v5}"
TARGET_COMMITISH="${TARGET_COMMITISH:-main}"

die() { echo "ERROR: $*" >&2; exit 1; }

[ -n "${GITEE_TOKEN:-}" ] || die "GITEE_TOKEN env var is required"
command -v gh   >/dev/null || die "gh not found"
command -v curl >/dev/null || die "curl not found"
command -v python >/dev/null || die "python not found"

# --- collect target tags ------------------------------------------------------
if [ "$#" -eq 0 ]; then
  die "no tags given. Pass tag names, or --all to sync every GitHub release."
fi

if [ "$1" = "--all" ]; then
  echo ">> fetching all release tags from $GH_REPO ..."
  mapfile -t TAGS < <(gh release list -R "$GH_REPO" --limit 1000 --json tagName --jq '.[].tagName')
else
  TAGS=("$@")
fi

echo ">> ${#TAGS[@]} release(s) to sync: ${TAGS[*]}"

# --- helpers ------------------------------------------------------------------

# json_get <field> : read a top-level JSON field from stdin
json_get() { python -c 'import sys,json; d=json.loads(sys.stdin.buffer.read()); print(d.get("'"$1"'","") if isinstance(d,dict) else "")'; }

# Return the Gitee release id for a tag, or empty string if it does not exist.
gitee_release_id() {
  local tag="$1" resp code body
  resp=$(curl -sS -w $'\n%{http_code}' \
    "$GITEE_API/repos/$GITEE_REPO/releases/tags/$tag?access_token=$GITEE_TOKEN")
  code=$(tail -n1 <<<"$resp")
  body=$(sed '$d' <<<"$resp")
  if [ "$code" = "200" ]; then
    printf '%s' "$body" | json_get id
  fi
}

# Create a Gitee release and echo its id.
gitee_create_release() {
  local tag="$1" name="$2" notes="$3" pre="$4" resp code body payload
  payload=$(TAG="$tag" NAME="$name" NOTES="$notes" PRE="$pre" \
            TOKEN="$GITEE_TOKEN" TARGET="$TARGET_COMMITISH" python -c '
import os,json
print(json.dumps({
  "access_token": os.environ["TOKEN"],
  "tag_name": os.environ["TAG"],
  "name": os.environ["NAME"] or os.environ["TAG"],
  "body": os.environ["NOTES"] or os.environ["TAG"],
  "prerelease": os.environ["PRE"] == "true",
  "target_commitish": os.environ["TARGET"],
}))')
  resp=$(curl -sS -w $'\n%{http_code}' -X POST \
    -H 'Content-Type: application/json' \
    "$GITEE_API/repos/$GITEE_REPO/releases" -d "$payload")
  code=$(tail -n1 <<<"$resp")
  body=$(sed '$d' <<<"$resp")
  if [ "$code" != "201" ] && [ "$code" != "200" ]; then
    echo "   create release failed (HTTP $code): $body" >&2
    return 1
  fi
  printf '%s' "$body" | json_get id
}

# List names of files already attached to a Gitee release.
gitee_attached_names() {
  local rid="$1"
  curl -sS "$GITEE_API/repos/$GITEE_REPO/releases/$rid/attach_files?access_token=$GITEE_TOKEN" \
    | python -c 'import sys,json
try:
    d=json.loads(sys.stdin.buffer.read())
    for a in (d if isinstance(d,list) else []):
        print(a.get("name",""))
except Exception:
    pass'
}

# Upload one file as an attachment.
gitee_upload() {
  local rid="$1" file="$2" resp code body
  resp=$(curl -sS -w $'\n%{http_code}' -X POST \
    "$GITEE_API/repos/$GITEE_REPO/releases/$rid/attach_files" \
    -F "access_token=$GITEE_TOKEN" -F "file=@$file")
  code=$(tail -n1 <<<"$resp")
  body=$(sed '$d' <<<"$resp")
  if [ "$code" = "201" ] || [ "$code" = "200" ]; then
    return 0
  fi
  echo "   upload failed (HTTP $code): $body" >&2
  return 1
}

# --- main loop ----------------------------------------------------------------
ok=0; skipped=0; failed=0

for tag in "${TAGS[@]}"; do
  echo
  echo "== $tag =="

  # Assets on the GitHub release
  mapfile -t assets < <(gh release view "$tag" -R "$GH_REPO" --json assets --jq '.assets[].name' 2>/dev/null || true)
  if [ "${#assets[@]}" -eq 0 ]; then
    echo "   no assets on GitHub release, skipping"
    skipped=$((skipped+1)); continue
  fi

  name=$(gh release view "$tag" -R "$GH_REPO" --json name --jq '.name' 2>/dev/null || echo "$tag")
  notes=$(gh release view "$tag" -R "$GH_REPO" --json body --jq '.body' 2>/dev/null || echo "")
  pre=$(gh release view "$tag" -R "$GH_REPO" --json isPrerelease --jq '.isPrerelease' 2>/dev/null || echo "false")

  # Download assets (or reuse a local directory when SRC_DIR is set)
  if [ -n "${SRC_DIR:-}" ]; then
    tmp="$SRC_DIR"
    echo "   using local assets from $tmp"
  else
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT
    echo "   downloading ${#assets[@]} asset(s) from GitHub ..."
    gh release download "$tag" -R "$GH_REPO" -D "$tmp" --clobber
  fi

  # Locate or create the Gitee release
  rid=$(gitee_release_id "$tag" || true)
  if [ -n "$rid" ]; then
    echo "   gitee release exists (id=$rid)"
  else
    echo "   creating gitee release ..."
    if ! rid=$(gitee_create_release "$tag" "$name" "$notes" "$pre"); then
      echo "   -> failed to create gitee release (is the tag mirrored to Gitee?)"
      failed=$((failed+1)); rm -rf "$tmp"; trap - EXIT; continue
    fi
    echo "   created gitee release (id=$rid)"
  fi

  # Upload, skipping files already attached
  mapfile -t attached < <(gitee_attached_names "$rid")
  tag_failed=0
  for base in "${assets[@]}"; do
    f="$tmp/$base"
    if [ ! -f "$f" ]; then
      echo "   ! $base (missing in $tmp)" >&2
      tag_failed=1
      continue
    fi
    if printf '%s\n' "${attached[@]}" | grep -qxF "$base"; then
      echo "   = $base (already attached, skip)"
      continue
    fi
    echo "   + $base"
    if ! gitee_upload "$rid" "$f"; then
      tag_failed=1
    fi
  done

  if [ -z "${SRC_DIR:-}" ]; then
    rm -rf "$tmp"; trap - EXIT
  fi
  if [ "$tag_failed" -eq 0 ]; then ok=$((ok+1)); else failed=$((failed+1)); fi
done

echo
echo ">> done. synced=$ok, skipped=$skipped, failed=$failed"
