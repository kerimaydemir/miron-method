#!/bin/sh
set -eu

if find . -type d -name node_modules \
  -not -path './.git/*' \
  -not -path '*/.next/*' \
  -not -path './apps/web/node_modules' \
  -print -quit | grep -q .; then
  echo "forbidden host dependency artifact found: node_modules" >&2
  exit 1
fi

if find . -type d -name .venv -not -path './.git/*' -print -quit | grep -q .; then
  echo "forbidden host dependency artifact found: .venv" >&2
  exit 1
fi

test -d apps/web/node_modules
test -z "$(find apps/web/node_modules -mindepth 1 -maxdepth 1 -print -quit)"

grep -q 'name: miron-baba-ai' compose.yaml
grep -q 'PRODUCT_NAME=MİRON BABA AI' .env.example
