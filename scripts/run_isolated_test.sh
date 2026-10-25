#!/bin/bash
# Reproduce the isolated test: a container network with no internet route, a mock vLLM backend,
# a LiteLLM proxy in front of it, and garak installed and run from the bundle (container_verify.sh).
# Usage, from the project root:  scripts/run_isolated_test.sh [extra garak args, e.g. --spec probes.dan]
# Env: ENGINE (docker|podman, default docker), LITELLM_IMG (LiteLLM proxy image to use).
set -euo pipefail

ENGINE=${ENGINE:-docker}
IMG=registry.access.redhat.com/ubi9/python-312:latest
LITELLM_IMG=${LITELLM_IMG:-ghcr.io/berriai/litellm-database:v1.90.2}
NET=garak-airgap
ROOT=$(pwd)
OUT=$ROOT/out/verify
mkdir -p "$OUT" && chmod 777 "$OUT"

cleanup() {
    $ENGINE rm -f garak-test-litellm garak-test-mock-vllm >/dev/null 2>&1 || true
    $ENGINE network rm "$NET" >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup

$ENGINE network create --internal "$NET" >/dev/null
$ENGINE run -d --name garak-test-mock-vllm --network "$NET" --platform linux/amd64 \
    -v "$ROOT/scripts:/scripts:ro" "$IMG" python3.12 -I /scripts/mock_litellm.py 8000 vllm-key 0.0.0.0 >/dev/null
$ENGINE run -d --name garak-test-litellm --network "$NET" -e LITELLM_LOCAL_MODEL_COST_MAP=True \
    -v "$ROOT/scripts/litellm-test-config.yaml:/app/config.yaml:ro" "$LITELLM_IMG" --config /app/config.yaml --port 4000 >/dev/null

for _ in $(seq 1 60); do
    $ENGINE logs garak-test-litellm 2>&1 | grep -q "Uvicorn running" && break
    sleep 2
done

$ENGINE run --rm --user 0 --platform linux/amd64 --network "$NET" \
    -e LITELLM_URL=http://garak-test-litellm:4000/v1 -e LITELLM_MODEL=my-model -e LITELLM_KEY=sk-litellm-test \
    -e GARAK_EXTRA_ARGS="$*" \
    -v "$ROOT/bundle:/bundle:ro" \
    -v "$ROOT/garak-offline.yaml:/cfg/garak-offline.yaml:ro" -v "$ROOT/garak-env.sh:/cfg/garak-env.sh:ro" \
    -v "$ROOT/scripts:/scripts:ro" -v "$ROOT/scripts/audit:/audit:ro" -v "$OUT:/out" \
    "$IMG" bash /scripts/container_verify.sh

echo "pickle audit events: $(wc -l < "$OUT/pickle-audit.log")"
echo "garak log and reports: $OUT/verify-data/garak/"
