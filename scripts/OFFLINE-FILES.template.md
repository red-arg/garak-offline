# garak offline bundle: files to download

Everything needed to run **garak 0.17.1** with its **default probe setup** on an isolated
**RHEL 9 / x86_64 / Python 3.12** host with **no network egress**. The model under test is
served by **vLLM behind LiteLLM** inside the isolated network, so its weights are *not* part of this bundle.

<!-- STATUS -->

## Summary

| # | Component | What | Size | Goes to (isolated host) |
|---|---|---|---|---|
| 1 | Python packages | `garak==0.17.1` from the internal package repository, CPU-only torch | not bundled | installed into a venv |
| 2 | Hugging Face models | 4 small classifier / attacker models, all safetensors | <!-- HF_MODEL_SIZE --> | `$HF_HOME/hub/` |
| 3 | Hugging Face datasets | 9 small datasets (package lists, system prompts) | <!-- HF_DATASET_SIZE --> | `$HF_HOME/hub/` (+ `$HF_HOME/datasets/`) |
| 4 | WordNet (Open English WordNet 2023) | 1 lexicon, loaded into a local database | <!-- WN_SIZE --> | `$XDG_CACHE_HOME/garak/data/wn/` |
| 5 | NLTK data | `averaged_perceptron_tagger_eng` (JSON, not pickle) | <!-- NLTK_SIZE --> | `$XDG_CACHE_HOME/garak/data/nltk_data/` |
| 6 | tiktoken encoding | `cl100k_base` (plain text) | <!-- TIKTOKEN_SIZE --> | `$TIKTOKEN_CACHE_DIR` (`$GARAK_HOME/cache/tiktoken/`) |
| 7 | Config (this folder) | `garak-offline.yaml`, `garak-env.sh`, `requirements.in`, `requirements.txt` | small | anywhere, e.g. `/opt/garak/` |

No model or data file in the bundle is in pickle format. The only pickle model garak would
normally use (`garak-llm/roberta_toxicity_classifier`, `pytorch_model.bin`) is replaced by
`garak-llm/toxic-comment-model` (safetensors) through `garak-offline.yaml`. Some Python packages
carry pickle files they never load; see [Pickle check](#pickle-check).

---

## 1. Python packages

Not bundled. Install `requirements.in` (`garak==0.17.1`) from the internal package repository:

```bash
python3.12 -m venv /opt/garak/venv
/opt/garak/venv/bin/pip install -r requirements.in
```

For the CPU-only torch build, add `--extra-index-url` pointing at the internal mirror of
`https://download.pytorch.org/whl/cpu`.

**Recommended: install the lock file instead.** `requirements.txt` pins all 178 packages with
hashes, including `torch==2.14.1+cpu`. It is exactly the set that passed the isolated test.
With only `requirements.in`, pip picks the newest versions of garak's dependencies on the day you
install. If PyPI has a newer torch than the CPU index, pip also picks the CUDA build from PyPI,
because `--extra-index-url` takes the highest version from any index.

```bash
/opt/garak/venv/bin/pip install --require-hashes -r requirements.txt \
  --index-url <internal PyPI mirror> --extra-index-url <internal mirror of download.pytorch.org/whl/cpu>
```

Two packages, `ecoji==0.1.1` and `langdetect==1.0.9`, are published only as source archives.
pip builds them during install, which needs `setuptools` from the same repository.

---

## 2. Hugging Face models

All are loaded on CPU by the `transformers` library. Download each at the pinned revision.

<!-- HF_MODELS -->

## 3. Hugging Face datasets

<!-- HF_DATASETS -->

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

<!-- WN_FILES -->

## 5. NLTK data

Used by `sata.MLM`. NLTK 3.10 loads this tagger from JSON files, not pickle.

NLTK 3.10 only reads and writes data in a directory that is not group- or world-writable,
including every parent directory. On the staging host, download it as a user whose home
directory is private (for example root), not into `/tmp` or a bind mount, then copy it into the bundle.

| Package | Source | Goes to |
|---|---|---|
| `averaged_perceptron_tagger_eng` | `https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger_eng.zip` | `cache/garak/data/nltk_data/taggers/` |

<!-- NLTK_FILES -->

## 6. tiktoken encoding: `cl100k_base`

Used by `divergence.RepeatedToken` through OpenAI's `tiktoken` library. Without it, tiktoken tries
to download the file at load time, the probe fails to load, and the rest of the run continues
without it. That was the only network access attempt in the isolated test.

| Source | Goes to |
|---|---|
| `https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken` (SHA-256 `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`) | `cache/tiktoken/9b5ad71b2ce5302211f9c61530b329a4922fc6a4`. The filename is the SHA-1 of the URL; tiktoken looks it up in `$TIKTOKEN_CACHE_DIR`, which `garak-env.sh` sets, and checks the SHA-256 before use. |

```bash
mkdir -p bundle/cache/tiktoken
curl -fL -o bundle/cache/tiktoken/9b5ad71b2ce5302211f9c61530b329a4922fc6a4 \
  https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken
```

<!-- TIKTOKEN_FILES -->

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
│   ├── tiktoken/               # section 6
│   └── garak/data/
│       ├── nltk_data/          # section 5
│       └── wn/                 # section 4
├── garak-offline.yaml
├── garak-env.sh
├── MANIFEST.md                 # generated file list with real names and sizes
└── SHA256SUMS                  # checksum of every file above
```

On the isolated host, unpack to `/opt/garak` (or set `GARAK_HOME`), then:

```bash
cd /opt/garak && sha256sum -c SHA256SUMS --quiet
export OPENAICOMPATIBLE_API_KEY=...        # LiteLLM key, from your secret store
source garak-env.sh
/opt/garak/venv/bin/garak --config garak-offline.yaml
```

Requirements on the isolated host:

- **Transfer as a `tar` archive.** The Hugging Face cache uses symlinks, which `tar` preserves.
- **The garak directory must not be group- or world-writable**, nor any of its parents
  (`chmod -R go-w /opt/garak`). NLTK 3.10 refuses to load data otherwise, and `sata.MLM` then
  fails to load. A root-owned `/opt/garak` with mode 755 is fine. Don't put it under `/tmp`, or
  under `/opt/app-root` in Red Hat UBI container images, which is group-writable.
- **No `HF_TOKEN` and no internet access are needed.** `garak-env.sh` puts the Hugging Face
  libraries in offline mode.

---

## Pickle check

**Bundle data: no pickle.** Every file under `cache/` was checked by content (pickle header, and
pickle entries inside zip files), not only by name. The models are safetensors, the datasets are
TSV, JSON(L) and Arrow, the NLTK tagger is JSON, WordNet is SQLite, and the tiktoken file is text.

**At runtime: nothing pickle-related is loaded.** During both isolated runs, a Python audit hook
logged every file opened with a pickle-type extension (`.pkl .pickle .pt .pth .bin .ckpt .joblib
.npy .npz`) and every class the `pickle` module looked up. Both logs are empty.

**Inside the Python packages: pickle files are present but never loaded.** A few packages from the
package repository ship pickle files:

| Package | Files | Loaded in a default run? |
|---|---|---|
| `garak` 0.17.1 | `garak/data/confidence_intervals/confidence_intervals.pkl` | No. No code in 0.17.1 reads it. |
| `garak` 0.17.1 | `garak/data/autodan/prompt_group.pth` | No. Only the live `dan.AutoDAN` attack loads it, and that probe isn't in the default set (the default uses `dan.AutoDANCached`). |
| `joblib` 1.6.0 | 30 files under `joblib/test/data/` | No (test fixtures) |
| `numpy` 2.5.4 | 8 files under `numpy/*/tests/data/` | No (test fixtures) |
| `torch` 2.14.1+cpu | `torch/bin/test_interpreter_async.pt` | No (test fixture) |

`setuptools`' `distutils-precedence.pth` matches by extension but is a Python path file, not a pickle.
If policy forbids pickle files on disk at all, delete these files from the venv after installing.
The default probe set doesn't need them.

---

## Configuration

### `garak-offline.yaml`

Set `target_name` to the model name LiteLLM exposes, and `uri` to the LiteLLM base URL.

```yaml
<!-- CFG_YAML -->
```

### `garak-env.sh`

```bash
<!-- CFG_ENV -->
```

---

## Producing the bundle

`scripts/container_harvest.sh` does sections 2–6 in one go on a connected staging host with
Docker or Podman, inside Red Hat's UBI 9 Python 3.12 image (RHEL 9 userspace):

```bash
podman run --rm --user 0 --platform linux/amd64 \
  -v ./bundle:/bundle -v ./scripts:/scripts:ro \
  -v ./garak-offline.yaml:/cfg/garak-offline.yaml:ro -v ./out:/out \
  registry.access.redhat.com/ubi9/python-312:latest bash /scripts/container_harvest.sh
```

It installs garak,
downloads the NLTK tagger, starts a stand-in OpenAI-compatible endpoint, and runs the default scan
once (1 generation per prompt) so every model, dataset and data file lands in `bundle/cache/`.
Afterwards:

```bash
rm -rf bundle/cache/huggingface/xet                       # download-only cache
python3 -I scripts/make_manifest.py bundle bundle/MANIFEST.md bundle/SHA256SUMS
cp requirements.in bundle/ && (cd bundle && sha256sum requirements.in >> SHA256SUMS)
```

`scripts/container_verify.sh` is the isolated test: on a network with no internet route, it checks
`SHA256SUMS`, installs the pinned packages from local wheels (standing in for the internal package
repository), and runs the default scan through LiteLLM using `garak-env.sh` and
`garak-offline.yaml` exactly as shipped. `scripts/run_isolated_test.sh` sets up that network with a
LiteLLM proxy and a mock vLLM backend, runs the test, and removes the containers afterwards.
Results go to `out/verify/`.

```bash
ENGINE=podman LITELLM_IMG=<your LiteLLM image> scripts/run_isolated_test.sh                  # full default run
ENGINE=podman LITELLM_IMG=<your LiteLLM image> scripts/run_isolated_test.sh --spec probes.lmrc   # a subset
```
