# Test-only audit hook: log every pickle-type file opened and every class pickle resolves.
# Activated by putting this directory on PYTHONPATH; writes to $PICKLE_AUDIT_LOG.
import os
import sys

_EXT = (".pkl", ".pickle", ".pt", ".pth", ".bin", ".ckpt", ".joblib", ".npy", ".npz")
_log = open(os.environ.get("PICKLE_AUDIT_LOG", "/dev/stderr"), "a", buffering=1)


def _hook(event, args):
    if event == "open" and args:
        try:
            path = os.fsdecode(os.fspath(args[0]))
        except TypeError:
            return  # file descriptor
        if path.lower().endswith(_EXT):
            _log.write(f"{os.getpid()} open {path}\n")
    elif event == "pickle.find_class":
        _log.write(f"{os.getpid()} pickle.find_class {args[0]}.{args[1]}\n")


sys.addaudithook(_hook)
