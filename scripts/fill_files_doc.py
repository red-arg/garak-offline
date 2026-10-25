"""Render OFFLINE-FILES.md from the template and the actual bundle contents.

Usage: python3 -I fill_files_doc.py <project_dir> <status_markdown>
"""

import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
status = sys.argv[2]
bundle = root / "bundle"
cache = bundle / "cache"
hub = cache / "huggingface" / "hub"
tpl = (root / "scripts" / "OFFLINE-FILES.template.md").read_text()
repos = json.loads((root / "scripts" / "hf_repos.json").read_text())

USED_BY = {
    "garak-llm/toxic-comment-model": "toxicity detector (`unsafe_content.ToxicCommentModel`): `atkgen.Tox`, `latentinjection.LatentJailbreak`, `lmrc.Bullying`, `realtoxicityprompts.RTPBlank`",
    "garak-llm/attackgeneration-toxicity_gpt2": "attacker model for `atkgen.Tox`",
    "garak-llm/refutation_detector_distilbert": "`misleading.MustRefuteClaimModel` for `misleading.FalseAssertion`",
    "garak-llm/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli": "`misleading.MustContradictNLI` (extended detector) for `misleading.FalseAssertion`",
    "garak-llm/pypi-20241031": "`packagehallucination.Python`",
    "garak-llm/npm-20241031": "`packagehallucination.JavaScript`",
    "garak-llm/rubygems-20241031": "`packagehallucination.Ruby`",
    "garak-llm/crates-20250307": "`packagehallucination.Rust`",
    "garak-llm/raku-20250811": "`packagehallucination.RakuLand`",
    "garak-llm/perl-20250811": "`packagehallucination.Perl`",
    "garak-llm/dart-20250811": "`packagehallucination.Dart`",
    "garak-llm/drh-System-Prompt-processed": "`sysprompt_extraction.SystemPromptExtraction`",
    "garak-llm/tm-system_prompt": "`sysprompt_extraction.SystemPromptExtraction`",
}
SKIP = {".gitattributes", "README.md"}


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_table(path, label):
    files = sorted(p for p in path.rglob("*") if p.is_file()) if path.exists() else []
    if not files:
        return f"_{label}: pending, collected when the staging run reaches this probe._", 0
    rows = ["| File | Size |", "|---|---|"]
    rows += [f"| `{p.relative_to(cache).as_posix()}` | {human(p.stat().st_size)} |" for p in files]
    return "\n".join(rows), sum(p.stat().st_size for p in files)


# 1. wheels
wheels = sorted((bundle / "wheels").glob("*.whl"))
wheel_rows = ["| # | Package | Version | File | Size | Source | SHA-256 |", "|---|---|---|---|---|---|---|"]
for i, w in enumerate(wheels, 1):
    name, ver = w.name.split("-")[:2]
    src = ("built from sdist" if name.lower() in ("ecoji", "langdetect")
           else "download.pytorch.org" if "+cpu" in ver else "PyPI")
    wheel_rows.append(f"| {i} | {name} | {ver} | `{w.name}` | {human(w.stat().st_size)} | {src} | `{sha256(w)}` |")

# 2/3. Hugging Face repos: collected files if present, else the repo's file list
def hf_table(kind):
    rows = ["| Repo | Revision | Used by | Files | Size | Status |", "|---|---|---|---|---|---|"]
    total = 0
    for r in (x for x in repos if x["kind"] == kind):
        snap = hub / f"{kind}--{r['repo'].replace('/', '--')}" / "snapshots" / r["sha"]
        if snap.exists():
            files = [(p.relative_to(snap).as_posix(), p.resolve().stat().st_size)
                     for p in sorted(snap.rglob("*")) if p.is_file()]
            state = "collected"
        else:
            files = [(f, s or 0) for f, s in r["files"] if f not in SKIP]
            state = "pending"
        size = sum(s for _, s in files)
        total += size
        listing = "<br>".join(f"`{f}` ({human(s)})" for f, s in files)
        rows.append(f"| `{r['repo']}` | `{r['sha']}` | {USED_BY[r['repo']]} | {listing} | {human(size)} | {state} |")
    return "\n".join(rows), total


models_md, models_size = hf_table("models")
datasets_md, datasets_size = hf_table("datasets")
ds_cache = cache / "huggingface" / "datasets"
if ds_cache.exists():
    ds_files = [p for p in ds_cache.rglob("*") if p.is_file() and not p.name.endswith(".lock")]
    ds_size = sum(p.stat().st_size for p in ds_files)
    datasets_md += f"\n\nPlus the processed copies `datasets` writes to `cache/huggingface/datasets/` ({len(ds_files)} files, {human(ds_size)})."
    datasets_size += ds_size

wn_md, wn_size = dir_table(cache / "garak" / "data" / "wn", "WordNet database")
nltk_md, nltk_size = dir_table(cache / "garak" / "data" / "nltk_data", "NLTK data")
tiktoken_md, tiktoken_size = dir_table(cache / "tiktoken", "tiktoken encoding")

out = tpl
for marker, value in {
    "STATUS": status,
    "WHEEL_COUNT": str(len(wheels)),
    "WHEEL_SIZE": human(sum(w.stat().st_size for w in wheels)),
    "WHEELS": "\n".join(wheel_rows),
    "HF_MODELS": models_md,
    "HF_MODEL_SIZE": human(models_size),
    "HF_DATASETS": datasets_md,
    "HF_DATASET_SIZE": human(datasets_size),
    "WN_FILES": wn_md,
    "WN_SIZE": human(wn_size) if wn_size else "pending",
    "NLTK_FILES": nltk_md,
    "NLTK_SIZE": human(nltk_size) if nltk_size else "pending",
    "TIKTOKEN_FILES": tiktoken_md,
    "TIKTOKEN_SIZE": human(tiktoken_size) if tiktoken_size else "pending",
    "CFG_YAML": (root / "garak-offline.yaml").read_text().strip(),
    "CFG_ENV": (root / "garak-env.sh").read_text().strip(),
}.items():
    out = out.replace(f"<!-- {marker} -->", value)

(root / "OFFLINE-FILES.md").write_text(out)
print("wrote", root / "OFFLINE-FILES.md")
