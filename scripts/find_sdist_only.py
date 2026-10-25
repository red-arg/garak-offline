"""List pinned requirements that have no wheel usable on RHEL9 x86_64 / CPython 3.12."""
import json, re, sys, urllib.request

req_file = sys.argv[1]
pins = re.findall(r"^([A-Za-z0-9_.\-]+)==([^\s\\]+)", open(req_file).read(), re.M)
ok_plat = re.compile(r"(manylinux[_0-9]*_x86_64|manylinux(1|2010|2014)_x86_64|linux_x86_64|any)$")
for name, ver in pins:
    if "+" in ver:  # local-version wheels (torch +cpu) come from the PyTorch index
        continue
    with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{ver}/json") as r:
        files = json.load(r)["urls"]
    usable = []
    for f in files:
        fn = f["filename"]
        if not fn.endswith(".whl"):
            continue
        py, abi, plat = fn[:-4].split("-")[-3:]
        if not any(ok_plat.search(p) for p in plat.split(".")):
            continue
        if abi in ("none", "abi3") or "cp312" in abi:
            if any(t in py for t in ("py3", "cp312", "py2.py3")) or abi == "abi3":
                usable.append(fn)
    if not usable:
        print(f"{name}=={ver}  sdist-only: {[f['filename'] for f in files]}")
