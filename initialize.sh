#!/bin/bash
# Initializes Tarang Electronics: venv -> deps (incl. the weave SDK from
# a sibling `weave/` checkout, needed by onboard.py) -> compile the weave
# SDK's own bundled core-client protos -> start the API.
#
# This is two things in one directory: a real HTTP API (api.py) standing
# in for "a business's own systems," and a one-time onboarding script
# (onboard.py) that uses the weave SDK to attach a subset of that API to
# a real running Weave core as tools + bot profiles. The API must be
# running (this script's default action) before onboard.py is run
# separately against it.
#
# Requires a sibling `weave/` checkout at ../weave (override with
# WEAVE_REPO) — this project depends on weave/packages/weave-sdk the way
# a real integrator would pre-release (editable/path dependency; swap for
# `pip install weave-sdk` once it's published, with zero other code
# changes). Unlike an earlier version of this script, there is no
# separate `weave/packages/shared-clients` install step: the weave SDK is
# self-contained (bundles its own generated gRPC stubs — see
# weave/packages/weave-sdk/weave/_core_client.py), and this project never
# imports shared-clients directly — installing both in the same venv
# would in fact break things (both compile the same core.data_access.v1/
# database.v1 proto packages into their own separate gen/ trees, and
# whichever loads first would silently shadow the other's).
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
SDK_DIR="$WEAVE_REPO/packages/weave-sdk"
SDK_GEN="$SDK_DIR/weave/gen"
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

echo "==> Installing dependencies (this API + weave SDK)"
"$PYTHON" -m pip install --upgrade pip --quiet
if command -v cygpath >/dev/null 2>&1; then
  SDK_WIN="$(cygpath -w "$SDK_DIR")"
else
  SDK_WIN="$SDK_DIR"
fi
"$PYTHON" -m pip install -e ".[dev]" --quiet
"$PYTHON" -m pip install -e "${SDK_WIN}[dev]" --quiet
# Pinned to match weave/'s own services exactly (not just >=) — see
# weave/PLAN.md Phase 3.8's note: grpcio-tools' generated _grpc.py stubs
# embed a minimum grpcio version check, so regenerating the SDK's gen/
# with a different grpcio-tools patch version than weave/'s other
# services can leave them unable to import it.
"$PYTHON" -m pip install grpcio==1.83.0 grpcio-tools==1.83.0 --quiet

echo "==> Compiling weave SDK's own bundled core-client protos (weave/gen)"
mkdir -p "$SDK_GEN"
"$PYTHON" -m grpc_tools.protoc \
  "-I$PROTOS_DIR" \
  "--python_out=$SDK_GEN" \
  "--grpc_python_out=$SDK_GEN" \
  "--pyi_out=$SDK_GEN" \
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
find "$SDK_GEN" -type d -exec touch {}/__init__.py \;

if [ "${1:-}" = "--setup-only" ]; then
  echo "==> Setup complete (--setup-only, not starting the API)"
  exit 0
fi

echo "==> Starting Tarang Electronics API on port ${DEMO_PORT:-9101}"
exec "$PYTHON" api.py
