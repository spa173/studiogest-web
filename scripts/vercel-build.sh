#!/bin/sh
set -eu

python=.vercel/python/.venv/bin/python

if [ "${VERCEL_ENV:-}" = production ]; then
    : "${DATABASE_URL_UNPOOLED:?Configura DATABASE_URL_UNPOOLED para las migraciones}"
    DATABASE_URL="$DATABASE_URL_UNPOOLED" "$python" manage.py migrate --noinput
fi

"$python" manage.py collectstatic --noinput
