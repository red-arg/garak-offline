"""Write the bundle manifest: every file to transfer, with size, SHA-256 and origin.

Usage: python3 -I make_manifest.py <bundle_dir> <manifest.md> <SHA256SUMS>
"""

import hashlib
import os
import re
import sys
from pathlib import Path

bundle, md_path, sums_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
PICKLE_EXT = (".bin", ".pt", ".pth", ".pkl", ".pickle", ".ckpt", ".joblib", ".npy", ".npz")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


sums, lines, pickles = [], [], []

# 1. Python wheels
wheels = sorted((bundle / "wheels").glob("*.whl"))
sdist_built = {"ecoji", "langdetect"}
lines += ["## 1. Python packages (`wheels/`)", "",
          f"{len(wheels)} wheels, {human(sum(w.stat().st_size for w in wheels))}. "
          "Install with `pip install --no-index --find-links wheels --require-hashes -r requirements-offline.txt`.", "",
          "| Package | Version | File | Size | Source |", "|---|---|---|---|---|"]
for w in wheels:
    name, ver = w.name.split("-")[:2]
    src = ("built from PyPI sdist" if name.lower() in sdist_built
           else "download.pytorch.org (CPU)" if "+cpu" in ver else "PyPI")
    lines.append(f"| {name} | {ver} | `{w.name}` | {human(w.stat().st_size)} | {src} |")
    sums.append((sha256(w), w.relative_to(bundle).as_posix()))

# 2. Hugging Face models / datasets (resolve snapshot symlinks to real names)
hub = bundle / "cache" / "huggingface" / "hub"
lines += ["", "## 2. Hugging Face models and datasets (`cache/huggingface/hub/`)", "",
          "| Repo | Type | Revision | Files (size) |", "|---|---|---|---|"]
for repo_dir in sorted(hub.glob("*--*")):
    kind, *parts = repo_dir.name.split("--")
    repo = "/".join(parts)
    for snap in sorted((repo_dir / "snapshots").glob("*")):
        files = []
        for f in sorted(p for p in snap.rglob("*") if p.is_file()):
            real = f.resolve()
            rel = f.relative_to(snap).as_posix()
            files.append(f"`{rel}` ({human(real.stat().st_size)})")
            if rel.lower().endswith(PICKLE_EXT):
                pickles.append(f"{repo}/{rel}")
        lines.append(f"| {repo} | {kind[:-1]} | `{snap.name[:12]}` | {', '.join(files)} |")
for f in sorted(p for p in hub.rglob("*") if p.is_file() and not p.is_symlink()):
    sums.append((sha256(f), f.relative_to(bundle).as_posix()))

# 3. Everything else under cache/ (datasets processed cache, garak cache: NLTK, WordNet, ...)
lines += ["", "## 3. Other cache data (`cache/`)", "", "| Path | Files | Size |", "|---|---|---|"]
other_root = bundle / "cache"
groups = {}
for f in sorted(p for p in other_root.rglob("*") if p.is_file() and not p.is_symlink()):
    rel = f.relative_to(other_root)
    if rel.parts[:2] in (("huggingface", "hub"), ("huggingface", "xet")):
        continue  # hub is listed above; xet is a download-only cache, not shipped
    key = "/".join(rel.parts[:4]) if rel.parts[0] == "garak" else "/".join(rel.parts[:3])
    n, size = groups.get(key, (0, 0))
    groups[key] = (n + 1, size + f.stat().st_size)
    sums.append((sha256(f), f.relative_to(bundle).as_posix()))
    if f.name.lower().endswith(PICKLE_EXT):
        pickles.append(rel.as_posix())
for key, (n, size) in sorted(groups.items()):
    lines.append(f"| `cache/{key}` | {n} | {human(size)} |")

total = sum((bundle / p).stat().st_size for _, p in sums)
header = [f"# garak offline bundle manifest", "",
          f"{len(sums)} files, {human(total)} total. Checksums: `SHA256SUMS` "
          f"(verify with `sha256sum -c SHA256SUMS` from the bundle directory).", "",
          "Pickle-format files: " + (", ".join(pickles) if pickles else "**none**"), ""]
md_path.write_text("\n".join(header + lines) + "\n")
sums_path.write_text("".join(f"{h}  {p}\n" for h, p in sorted(sums, key=lambda x: x[1])))
print(f"{len(sums)} files, {human(total)}; pickle files: {pickles or 'none'}")
