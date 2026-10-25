#!/bin/bash
# Isolation test, run inside UBI9 python-312 (linux/amd64) on a Docker --internal network:
# no route to the internet, only the LiteLLM proxy is reachable.
# Installs and runs garak using only the bundle, garak-env.sh and garak-offline.yaml.
# Run as root (--user 0) so /opt/garak is root-owned and not group/world-writable, as on the real host.
# Mounts: /bundle (ro), /cfg (ro), /out (rw), /audit (ro, test-only pickle audit hook). Env: LITELLM_URL, LITELLM_MODEL, LITELLM_KEY
set -euo pipefail

if python3.12 -I -c "import socket; socket.create_connection(('pypi.org', 443), timeout=5)" 2>/dev/null; then
    echo "EGRESS AVAILABLE - not an isolated test, aborting"; exit 1
fi
echo "confirmed: no internet egress"

(cd /bundle && sha256sum -c SHA256SUMS --quiet) && echo "bundle checksums OK"

mkdir -p /opt/garak && chmod 755 /opt/garak
python3.12 -m venv /opt/garak/venv
/opt/garak/venv/bin/pip install -q --no-index --find-links /bundle/wheels --require-hashes -r /bundle/requirements-offline.txt
cp -a /bundle/cache /opt/garak/cache

export HOME=/root GARAK_HOME=/opt/garak OPENAICOMPATIBLE_API_KEY=$LITELLM_KEY
source /cfg/garak-env.sh
export XDG_DATA_HOME=/out/verify-data

sed -e "s#https://litellm.internal.example.com/v1#$LITELLM_URL#" \
    -e "s#target_name: my-model#target_name: $LITELLM_MODEL#" \
    /cfg/garak-offline.yaml > /opt/garak-verify.yaml

set +e
PYTHONPATH=/audit PICKLE_AUDIT_LOG=/out/pickle-audit.log /opt/garak/venv/bin/garak --config /opt/garak-verify.yaml --generations 1 --report_prefix verify 2>&1 | tee /out/verify-console.log
echo "garak exit: ${PIPESTATUS[0]}"
