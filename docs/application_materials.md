# Application materials

All statements below describe what this repository implements and what has been executed in
it. If the suite changes, update the numbers.

## Short GitHub project description

Hardware-free pytest regression suite for NXP SPSDK's `nxpcrypto` CLI: ECDSA P-256 signing,
tamper detection, negative security tests, independent verification, and GitHub Actions CI.

## CV project entry

**SPSDK Security Regression Lab** | Python, pytest, NXP SPSDK, GitHub Actions |
github.com/Joun-Mikhail/spsdk-security-regression-lab

- Built a Python/pytest regression suite of 28 automated test cases (12 scenarios) that runs the
  real NXP SPSDK 3.13.0 `nxpcrypto` CLI to check ECDSA P-256 key generation, firmware signing,
  signature verification and SHA-256 digests.
- Wrote 15 negative security tests (tampered firmware, wrong public key, corrupted or truncated
  signatures, malformed keys, missing files). Each one uses a positive control and an explicit
  ACCEPTED/REJECTED/ERROR verdict, because SPSDK's verify command exits with code 0 even when a
  signature is invalid.
- Cross-checked SPSDK results with an independent oracle (Python `cryptography`, `hashlib`) and
  automated Ruff and pytest in GitHub Actions. A deliberate harness defect made 7 tests fail,
  which showed the suite catches regressions.

## Motivation paragraph (about 100 words)

I am an Electrical Engineering student at Brno University of Technology. To understand the work
of a security software test engineer, I built a small regression suite around NXP's open-source
SPSDK. It runs the real `nxpcrypto` tool, checks that valid firmware signatures are accepted, and
confirms that tampered firmware, wrong keys and damaged signatures are rejected. The most useful
lesson came from a surprise: the verify command returns exit code 0 even for an invalid signature.
That taught me to prove a test really exercised what it claims to check. I would like to develop
that habit further in NXP's Security Software Test Engineering internship.

## LinkedIn project description

**SPSDK Security Regression Lab**: an independent, hardware-free test suite for the cryptographic
command-line tools in NXP's open-source Secure Provisioning SDK. It signs and verifies synthetic
firmware with ECDSA P-256, checks SHA-256 digests, and feeds the tool invalid inputs (tampered
firmware, wrong keys, corrupted signatures) to confirm they are rejected. An independent Python
`cryptography` oracle cross-checks the results, and GitHub Actions runs Ruff and pytest on every
change. This is a personal learning project, not affiliated with NXP.

## 45-second technical interview explanation

"Secure boot only works if the signing tools accept good firmware and reject modified firmware.
My project tests that for the `nxpcrypto` tool in NXP's SPSDK. Pytest drives the real CLI through
`subprocess`. It generates a P-256 key, signs a synthetic firmware file, and verifies it. Then the
negative tests change one thing each time: one firmware byte, the public key, or the signature.
Each change must be rejected. I found that verify returns exit code 0 even for a bad signature,
so my harness reads the actual verdict, runs a positive control first, and treats CLI errors as
failures, not as rejections. Every signature is also checked independently with Python's
`cryptography` library, and GitHub Actions runs everything on each push. It's host-side only:
there's no chip or boot ROM involved."
