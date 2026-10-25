> **Status (2026-10-25): isolated test passed.**
> - **Setup:** a RHEL 9.8 (UBI 9) x86_64 container on a Docker network with no internet route. garak called a real LiteLLM proxy (API-key auth), which forwarded to a mock vLLM backend.
> - **All 93 default probes ran offline.** 92 ran in the full run (31 min, 1 generation per prompt, exit 0). `divergence.RepeatedToken` ran in a follow-up run after its tiktoken file was added (section 6).
> - **Network:** the only access attempt in the full run was tiktoken's, now fixed. The Perspective API detectors are skipped as expected.
> - **Pickle:** an audit hook recorded no pickle-type file opened and no pickle class loaded in either run.
> - **Bundle:** `SHA256SUMS` was verified inside the isolated container. Every model and data file was downloaded by garak itself during the staging run.
> - **Python packages:** the test installed the 178 hash-pinned packages from `requirements.txt` as local wheels, standing in for the internal package repository.
