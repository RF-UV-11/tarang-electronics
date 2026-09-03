#!/bin/bash
# Initializes Tarang Electronics: venv -> deps (incl. the weave SDK +
# shared-clients from a sibling `weave/` checkout, needed by onboard.py)
# -> compile the core-client protos into shared-clients -> start the API.
#
# This is two things in one directory: a real HTTP API (api.py) standing
# in for "a business's own systems," and a one-time onboarding script
# (onboard.py) that uses the weave SDK to attach a subset of that API to
# a real running Weave core as tools + bot profiles. The API must be
# running (this script's default action) before onboard.py is run
# separately against it.
#
# Requires a sibling `weave/` checkout at ../weave (override with
# WEAVE_REPO) — this project depends on weave/packages/weave-sdk and
# weave/packages/shared-clients the way a real integrator would
# pre-release (editable/path dependency; swap for `pip install
# weave-sdk` once it's published, with zero other code changes).
#
# Usage:
#   ./initialize.sh                # full setup + start the demo API
#   ./initialize.sh --setup-only   # setup only, don't start the API
#
# Config: DEMO_PORT (default 9101), WEAVE_REPO (default ../weave).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEAVE_REPO="${WEAVE_REPO:-$(cd "$DIR/../weave" && pwd)}"
PROTOS_DIR="$WEAVE_REPO/protos"
SHARED_CLIENTS_DIR="$WEAVE_REPO/packages/shared-clients"
SHARED_CLIENTS_GEN="$SHARED_CLIENTS_DIR/weave_shared_clients/gen"
SDK_DIR="$WEAVE_REPO/packages/weave-sdk"
VENV_DIR="$DIR/.venv"

cd "$DIR"

if [ ! -d "$WEAVE_REPO/packages/weave-sdk" ]; then
  echo "error: no weave/ checkout found at $WEAVE_REPO (set WEAVE_REPO to override)" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtualenv at $VENV_DIR"
  python -m venv "$VENV_DIR"
fi

if [ -f "$VENV_DIR/Scripts/python.exe" ]; then
  PYTHON="$VENV_DIR/Scripts/python.exe"
else
  PYTHON="$VENV_DIR/bin/python"
fi

echo "==> Installing dependencies (this API + weave SDK + shared-clients)"
"$PYTHON" -m pip install --upgrade pip --quiet
if command -v cygpath >/dev/null 2>&1; then
  SHARED_CLIENTS_WIN="$(cygpath -w "$SHARED_CLIENTS_DIR")"
  SDK_WIN="$(cygpath -w "$SDK_DIR")"
else
  SHARED_CLIENTS_WIN="$SHARED_CLIENTS_DIR"
  SDK_WIN="$SDK_DIR"
fi
"$PYTHON" -m pip install -e ".[dev]" --quiet
"$PYTHON" -m pip install -e "${SHARED_CLIENTS_WIN}[dev]" --quiet
"$PYTHON" -m pip install -e "${SDK_WIN}[dev]" --quiet
# Pinned to match weave/'s own services exactly (not just >=) — see
# weave/PLAN.md Phase 3.8's note: grpcio-tools' generated _grpc.py stubs
# embed a minimum grpcio version check, so regenerating shared-clients'
# gen/ with a different grpcio-tools patch version than weave/'s other
# services can leave them unable to import it.
"$PYTHON" -m pip install grpcio==1.83.0 grpcio-tools==1.83.0 --quiet

echo "==> Compiling core client protos into shared-clients"
mkdir -p "$SHARED_CLIENTS_GEN"
"$PYTHON" -m grpc_tools.protoc \
  "-I$PROTOS_DIR" \
  "--python_out=$SHARED_CLIENTS_GEN" \
  "--grpc_python_out=$SHARED_CLIENTS_GEN" \
  "--pyi_out=$SHARED_CLIENTS_GEN" \
  "$PROTOS_DIR/database/v1/common.proto" \
  "$PROTOS_DIR/database/v1/tenant.proto" \
  "$PROTOS_DIR/database/v1/connector.proto" \
  "$PROTOS_DIR/database/v1/credential.proto" \
  "$PROTOS_DIR/database/v1/auth.proto" \
  "$PROTOS_DIR/database/v1/bot_profile.proto" \
  "$PROTOS_DIR/database/v1/http_tool.proto" \
  "$PROTOS_DIR/core/data_access/v1/tenant.proto" \
  "$PROTOS_DIR/core/data_access/v1/connector.proto" \
  "$PROTOS_DIR/core/data_access/v1/auth.proto" \
  "$PROTOS_DIR/core/data_access/v1/bot_profile.proto" \
  "$PROTOS_DIR/core/data_access/v1/http_tool.proto"
find "$SHARED_CLIENTS_GEN" -type d -exec touch {}/__init__.py \;

if [ "${1:-}" = "--setup-only" ]; then
  echo "==> Setup complete (--setup-only, not starting the API)"
  exit 0
fi

echo "==> Starting Tarang Electronics API on port ${DEMO_PORT:-9101}"
exec "$PYTHON" api.py
