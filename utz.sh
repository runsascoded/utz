#!/usr/bin/env bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
call_dir="$(pwd)"

if ! cd "$script_dir"; then
  echo "Error cd'ing into \"$script_dir\"" >&2
  exit 1
fi

python -m utz.run -d "$call_dir" "$@"
