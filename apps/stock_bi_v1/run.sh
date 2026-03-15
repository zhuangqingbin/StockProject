#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
exec python3 -m apps.stock_bi_v1.run
