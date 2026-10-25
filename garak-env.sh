# Source this before running garak in the isolated environment:  source garak-env.sh
# GARAK_HOME is where the bundle's cache/ directory was unpacked.
export GARAK_HOME=${GARAK_HOME:-/opt/garak}

# Where garak and Hugging Face find the pre-seeded files
export HF_HOME=$GARAK_HOME/cache/huggingface    # detector/attacker models + datasets
export XDG_CACHE_HOME=$GARAK_HOME/cache          # garak cache: NLTK data, WordNet DB
export XDG_DATA_HOME=$GARAK_HOME/data            # garak reports: $XDG_DATA_HOME/garak/garak_runs
export TIKTOKEN_CACHE_DIR=$GARAK_HOME/cache/tiktoken  # cl100k_base encoding for divergence.RepeatedToken

# Never try the network for models/datasets; fail fast instead of waiting on timeouts
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
# litellm is a garak dependency; stop it fetching its price list from GitHub if it is ever imported
export LITELLM_LOCAL_MODEL_COST_MAP=True

# LiteLLM API key for the target (read by garak's openai.OpenAICompatible generator).
# Prefer injecting this from your secret store rather than writing it here.
export OPENAICOMPATIBLE_API_KEY=${OPENAICOMPATIBLE_API_KEY:?set OPENAICOMPATIBLE_API_KEY to the LiteLLM key}

# If LiteLLM uses a certificate from an internal CA, trust the RHEL system bundle
# (add the CA with update-ca-trust first). The OpenAI client otherwise uses certifi's bundle.
# export SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt

# If the host has an HTTP(S)_PROXY set globally, make sure the LiteLLM host bypasses it:
# export NO_PROXY=litellm.internal.example.com,$NO_PROXY
