#!/usr/bin/env bash
# Portable in-place sed helper for GNU sed and BSD sed (macOS).

sed_inplace() {
    local file="$1"
    shift

    [ -f "$file" ] || return 1

    local tmp="${file}.tmp.$$"
    if sed "$@" "$file" > "$tmp"; then
        # Write through the existing inode so ownership and permissions are kept.
        if cat "$tmp" > "$file"; then
            rm -f "$tmp"
            return 0
        fi
    fi

    rm -f "$tmp"
    return 1
}
