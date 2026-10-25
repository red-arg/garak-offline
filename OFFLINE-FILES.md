# garak offline bundle: files to download

Everything needed to run **garak 0.17.1** with its **default probe setup** on an isolated
**RHEL 9 / x86_64 / Python 3.12** host with **no network egress**. The model under test is
served by **vLLM behind LiteLLM** inside the isolated network, so its weights are *not* part of this bundle.

> **Status (2026-10-25)**
> - **Python packages: not bundled.** Installed from the internal package repository.
> - **Models: collected.** All 4 Hugging Face models were downloaded by garak itself during the staging run (rows marked *collected*).
> - **Datasets, WordNet, NLTK: collection run in progress.** Rows marked *pending* come from garak's source and plugin metadata and will be confirmed when the run reaches those probes.
> - **End-to-end isolated test: not run yet.** This is a run on a network with no internet route, through a real LiteLLM proxy. This document will be regenerated once it passes.

## Summary

| # | Component | What | Size | Goes to (isolated host) |
|---|---|---|---|---|
| 1 | Python packages | `garak==0.17.1` from the internal package repository, CPU-only torch | not bundled | installed into a venv |
| 2 | Hugging Face models | 4 small classifier / attacker models, all safetensors | 2.3 GB | `$HF_HOME/hub/` |
| 3 | Hugging Face datasets | 9 small datasets (package lists, system prompts) | 192.4 MB | `$HF_HOME/hub/` (+ `$HF_HOME/datasets/`) |
| 4 | WordNet (Open English WordNet 2023) | 1 lexicon, loaded into a local database | pending | `$XDG_CACHE_HOME/garak/data/wn/` |
| 5 | NLTK data | `averaged_perceptron_tagger_eng` (JSON, not pickle) | pending | `$XDG_CACHE_HOME/garak/data/nltk_data/` |
| 6 | Config (this folder) | `garak-offline.yaml`, `garak-env.sh`, `requirements.in` | small | anywhere, e.g. `/opt/garak/` |

No file in the bundle is in pickle format. The only pickle model garak would normally use
(`garak-llm/roberta_toxicity_classifier`, `pytorch_model.bin`) is replaced by
`garak-llm/toxic-comment-model` (safetensors) through `garak-offline.yaml`.

---

## 1. Python packages

Not bundled. Install `requirements.in` (`garak==0.17.1`) from the internal package repository:

```bash
python3.12 -m venv /opt/garak/venv
/opt/garak/venv/bin/pip install -r requirements.in
```

For the CPU-only torch build, add `--extra-index-url` pointing at the internal mirror of
`https://download.pytorch.org/whl/cpu`.

---

## 2. Hugging Face models

All are loaded on CPU by the `transformers` library. Download each at the pinned revision.

| Repo | Revision | Used by | Files | Size | Status |
|---|---|---|---|---|---|
| `garak-llm/toxic-comment-model` | `9088b7ea740ef33552f8225007c5768fd17d67c8` | toxicity detector (`unsafe_content.ToxicCommentModel`): `atkgen.Tox`, `latentinjection.LatentJailbreak`, `lmrc.Bullying`, `realtoxicityprompts.RTPBlank` | `config.json` (704 B)<br>`model.safetensors` (255.4 MB)<br>`special_tokens_map.json` (112 B)<br>`tokenizer.json` (455.2 KB)<br>`tokenizer_config.json` (403 B)<br>`vocab.txt` (226.1 KB) | 256.1 MB | collected |
| `garak-llm/attackgeneration-toxicity_gpt2` | `565f41dd443592c2146a604211468974d7a7d1a7` | attacker model for `atkgen.Tox` | `config.json` (914 B)<br>`generation_config.json` (124 B)<br>`merges.txt` (445.6 KB)<br>`model.safetensors` (474.7 MB)<br>`special_tokens_map.json` (99 B)<br>`tokenizer.json` (2.0 MB)<br>`tokenizer_config.json` (234 B)<br>`vocab.json` (779.4 KB) | 477.9 MB | collected |
| `garak-llm/refutation_detector_distilbert` | `906ac60cba379abc1ad1ed328acebeb17357adac` | `misleading.MustRefuteClaimModel` for `misleading.FalseAssertion` | `config.json` (604 B)<br>`model.safetensors` (255.4 MB)<br>`special_tokens_map.json` (125 B)<br>`tokenizer.json` (694.7 KB)<br>`tokenizer_config.json` (320 B)<br>`vocab.txt` (226.1 KB) | 256.3 MB | collected |
| `garak-llm/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli` | `75044664e962c6237d48ec4d72fa189fb8723fdc` | `misleading.MustContradictNLI` (extended detector) for `misleading.FalseAssertion` | `config.json` (703 B)<br>`merges.txt` (445.6 KB)<br>`model.safetensors` (1.3 GB)<br>`special_tokens_map.json` (772 B)<br>`tokenizer_config.json` (49 B)<br>`vocab.json` (877.8 KB) | 1.3 GB | collected |

## 3. Hugging Face datasets

| Repo | Revision | Used by | Files | Size | Status |
|---|---|---|---|---|---|
| `garak-llm/pypi-20241031` | `d0cb6954a12ebe3e383e9946ab2685efa23130fa` | `packagehallucination.Python` | `pypi-20241031.tsv` (21.8 MB) | 21.8 MB | pending |
| `garak-llm/npm-20241031` | `98e02cd0a2d568a8b36300431aefba21550a9d34` | `packagehallucination.JavaScript` | `npm-20241031.tsv` (151.4 MB) | 151.4 MB | pending |
| `garak-llm/rubygems-20241031` | `51ab0238f9c16b5c31ecfdf935da9fd5abf74647` | `packagehallucination.Ruby` | `rubygems-20241031.tsv` (6.9 MB) | 6.9 MB | pending |
| `garak-llm/crates-20250307` | `36751f99fd6652a029c8b26ddd2ffcf745f4d999` | `packagehallucination.Rust` | `crates-20250307.tsv` (5.6 MB) | 5.6 MB | pending |
| `garak-llm/raku-20250811` | `e2b0b34ad3cb30e6c62076f4cfeb605c94f3a809` | `packagehallucination.RakuLand` | `raku_packages_dataset.jsonl` (56.2 KB) | 56.2 KB | pending |
| `garak-llm/perl-20250811` | `2b41fd08111f283b03d00544121ba438c769db22` | `packagehallucination.Perl` | `create_dataset.py` (1.7 KB)<br>`perl_modules_dataset.jsonl` (2.1 MB) | 2.2 MB | pending |
| `garak-llm/dart-20250811` | `f50076de413a4f660d65b398096fae750b35d53b` | `packagehallucination.Dart` | `create_dataset.py` (1.2 KB)<br>`dart_output.log` (1.1 MB)<br>`dart_packages_dataset.jsonl` (1.8 MB) | 2.9 MB | pending |
| `garak-llm/drh-System-Prompt-processed` | `26bb2b284b0380268bc74fe51b1c5eeaccb02242` | `sysprompt_extraction.SystemPromptExtraction` | `drh.json` (1.4 MB) | 1.4 MB | pending |
| `garak-llm/tm-system_prompt` | `005c0854fe0c95e6a56ed45e3ff1e755cf007394` | `sysprompt_extraction.SystemPromptExtraction` | `final_system_prompts_69.jsonl` (15.2 KB) | 15.2 KB | pending |

**How to download 2 and 3:** the reliable way is to run garak once on a staging host with the
same config against a stand-in endpoint, so every probe and detector downloads exactly the files it
loads, already in the cache layout garak expects (see [Producing the bundle](#producing-the-bundle)).
Downloading by hand with `hf download <repo> --revision <sha>` into `$HF_HOME` also works for the
models; datasets also need the processed copy that `datasets.load_dataset` writes, which only the
staging run produces.

Leave out `huggingface/xet/`. It's a download cache that offline loading doesn't use.

## 4. WordNet: Open English WordNet 2023

Used by `topic.WordnetControversial` through the `wn` package (not NLTK).

| Source | Used as |
|---|---|
| `https://en-word.net/static/english-wordnet-2023.xml.gz` (mirror: `https://github.com/globalwordnet/english-wordnet/releases/download/2023-edition/english-wordnet-2023.xml.gz`) | Loaded into `cache/garak/data/wn/` (SQLite database). Ship the built directory; the XML isn't needed afterwards. |

_WordNet database: pending, collected when the staging run reaches this probe._

## 5. NLTK data

Used by `sata.MLM`. NLTK 3.10 loads this tagger from JSON files, not pickle.

| Package | Source | Goes to |
|---|---|---|
| `averaged_perceptron_tagger_eng` | `https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger_eng.zip` | `cache/garak/data/nltk_data/taggers/` |

_NLTK data: pending, collected when the staging run reaches this probe._

---

## Not downloaded (intentionally)

| Item | Why |
|---|---|
| `garak-llm/roberta_toxicity_classifier` | Pickle-only (`pytorch_model.bin`). Replaced by `garak-llm/toxic-comment-model` in `garak-offline.yaml`. |
| Your model's weights | Served by vLLM; garak only calls the LiteLLM endpoint. |
| Perspective API detectors (`perspective.Toxicity`, `perspective.Sexually_Explicit`) | Google cloud service. garak runs them as *extra* detectors for `lmrc.SexualContent`, `lmrc.Sexualisation` and `realtoxicityprompts.RTPBlank`; without a key it logs `detector load failed … skipping` and scores those probes with their primary detector. |
| CUDA / NVIDIA packages | torch is the CPU build. GPU work happens on the vLLM server; garak's own models are small enough for CPU. |
| Attacker models for non-default probes (`tap.TAP`, `goat`, `dan.AutoDAN`, `fitd`, …) | Not part of the default probe set. |
| `huggingface/xet/` | Download-only cache. |

---

## Bundle layout

```
garak-bundle/
├── requirements.in             # garak==0.17.1
├── cache/
│   ├── huggingface/hub/        # sections 2 and 3
│   ├── huggingface/datasets/   # processed datasets (section 3)
│   └── garak/data/
│       ├── nltk_data/          # section 5
│       └── wn/                 # section 4
├── garak-offline.yaml
├── garak-env.sh
└── SHA256SUMS                  # checksum of every file above
```

On the isolated host, unpack to `/opt/garak` (or set `GARAK_HOME`), then:

```bash
cd /opt/garak && sha256sum -c SHA256SUMS --quiet
export OPENAICOMPATIBLE_API_KEY=...        # LiteLLM key, from your secret store
source garak-env.sh
/opt/garak/venv/bin/garak --config garak-offline.yaml
```

Transfer it as a `tar` archive: the Hugging Face cache uses symlinks, which `tar` preserves.

---

## Configuration

### `garak-offline.yaml`

Set `target_name` to the model name LiteLLM exposes, and `uri` to the LiteLLM base URL.

```yaml
---
# garak 0.17.1 - default probe set, run fully offline against a vLLM model behind LiteLLM.
# Run with:  source garak-env.sh && garak --config garak-offline.yaml

run:
  generations: 5            # garak default; responses requested per prompt

# garak sends one request at a time by default. To run attempts in parallel, uncomment
# both lines (size it to what your vLLM / LiteLLM rate limits allow). Don't leave
# "system:" uncommented on its own - garak 0.17.1 fails on an empty section.
# system:
#   parallel_attempts: 16

plugins:
  target_type: openai.OpenAICompatible
  target_name: my-model     # the model name exactly as LiteLLM exposes it (GET /v1/models)
  generators:
    openai:
      OpenAICompatible:
        uri: https://litellm.internal.example.com/v1
        # The API key is read from the OPENAICOMPATIBLE_API_KEY environment variable.
        # If LiteLLM rejects the "n" parameter, uncomment:
        # suppressed_params: ["n"]
  detectors:
    unsafe_content:
      ToxicCommentModel:
        # Pickle-free replacement for garak's default toxicity classifier
        # (default garak-llm/roberta_toxicity_classifier ships only pytorch_model.bin).
        detector_model_path: garak-llm/toxic-comment-model
```

### `garak-env.sh`

```bash
# Source this before running garak in the isolated environment:  source garak-env.sh
# GARAK_HOME is where the bundle's cache/ directory was unpacked.
export GARAK_HOME=${GARAK_HOME:-/opt/garak}

# Where garak and Hugging Face find the pre-seeded files
export HF_HOME=$GARAK_HOME/cache/huggingface    # detector/attacker models + datasets
export XDG_CACHE_HOME=$GARAK_HOME/cache          # garak cache: NLTK data, WordNet DB
export XDG_DATA_HOME=$GARAK_HOME/data            # garak reports: $XDG_DATA_HOME/garak/garak_runs

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
```

---

## Producing the bundle

`scripts/container_harvest.sh` does sections 2–5 in one go on a connected staging host with
Docker or Podman, inside Red Hat's UBI 9 Python 3.12 image (RHEL 9 userspace):

```bash
podman run --rm --platform linux/amd64 \
  -v ./bundle:/bundle -v ./scripts:/scripts:ro \
  -v ./garak-offline.yaml:/cfg/garak-offline.yaml:ro -v ./out:/out \
  registry.access.redhat.com/ubi9/python-312:latest bash /scripts/container_harvest.sh
```

It installs garak,
starts a stand-in OpenAI-compatible endpoint, and runs the default scan once (1 generation per
prompt) so every model, dataset and data file lands in `bundle/cache/`.
`scripts/make_manifest.py` then writes `SHA256SUMS` and flags any pickle files.
