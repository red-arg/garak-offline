"""Write a hash-pinned requirements file for exactly the wheels in a directory.

Usage: python3 -I make_offline_lock.py <wheels_dir> > requirements-offline.txt
"""

import hashlib
import re
import sys
from pathlib import Path

wheels = sorted(Path(sys.argv[1]).glob("*.whl"))
for whl in wheels:
    name, version = whl.name.split("-")[:2]
    name = re.sub(r"[-_.]+", "-", name).lower()
    digest = hashlib.sha256(whl.read_bytes()).hexdigest()
    print(f"{name}=={version} --hash=sha256:{digest}")
print(f"# {len(wheels)} wheels", file=sys.stderr)
