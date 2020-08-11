#!/usr/bin/env bash

dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
parent="$(cd "$(dirname "$dir")" && pwd)"
name="$(basename "$dir")"
prev="$(pwd)"
cd "$parent"
python -m "$name".run -d "$prev" "$@"
