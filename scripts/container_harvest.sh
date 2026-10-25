#!/bin/bash
# Staging step, run inside UBI9 python-312 (linux/amd64) WITH network access.
# Builds wheels for the two sdist-only packages, installs garak from the bundle,
# then runs the default scan against a mock endpoint so every probe/detector
# downloads what it needs into the bundle's cache.
# Run as root (--user 0): NLTK 3.10 only writes to private directories (no group/world-writable
# ancestors), and root's home is the private directory available in the UBI image.
# Mounts: /bundle (rw), /scripts (ro), /cfg (ro), /out (rw)
set -euo pipefail

B=/bundle
cd /tmp

python3.12 -m pip wheel -q --no-deps -w "$B/wheels" "$B"/sdist/*.tar.gz
python3.12 -I /scripts/make_offline_lock.py "$B/wheels" > "$B/requirements-offline.txt"

python3.12 -m venv /tmp/venv
/tmp/venv/bin/pip install -q --no-index --find-links "$B/wheels" --require-hashes -r "$B/requirements-offline.txt"

export HOME=/root
export HF_HOME=$B/cache/huggingface XDG_CACHE_HOME=$B/cache XDG_DATA_HOME=/out/harvest-data
export TIKTOKEN_CACHE_DIR=$B/cache/tiktoken
export HF_HUB_DISABLE_TELEMETRY=1 LITELLM_LOCAL_MODEL_COST_MAP=True
export OPENAICOMPATIBLE_API_KEY=harvest-key
mkdir -p "$HOME"

# NLTK refuses bind-mounted targets whose real path differs (e.g. Docker Desktop), so
# download into the private home directory and copy into the bundle.
/tmp/venv/bin/python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng', download_dir='$HOME/nltk_data', quiet=True)"
mkdir -p "$B/cache/garak/data/nltk_data" && cp -r "$HOME/nltk_data/." "$B/cache/garak/data/nltk_data/"

python3.12 -I /scripts/mock_litellm.py 4000 harvest-key &
sleep 2

sed -e 's#https://litellm.internal.example.com/v1#http://127.0.0.1:4000/v1#' \
    -e 's#target_name: my-model#target_name: mock-model#' \
    /cfg/garak-offline.yaml > /tmp/garak-harvest.yaml

set +e
/tmp/venv/bin/garak --config /tmp/garak-harvest.yaml --generations 1 --report_prefix harvest 2>&1 | tee /out/harvest-console.log
echo "garak exit: ${PIPESTATUS[0]}"
python3.12 -I -c "import urllib.request; print('mock stats:', urllib.request.urlopen('http://127.0.0.1:4000/v1/stats').read().decode())"
