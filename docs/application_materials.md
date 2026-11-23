# Application materials

All statements below describe what the repository implements and what has been executed. Update
the numbers if the suite changes.

## A. GitHub project description

Independent Python regression testing framework for cryptographic workflows in NXP Secure
Provisioning SDK, featuring negative security tests, independent verification, and GitHub Actions
CI.

## B. CV project entry

**SPSDK Security Regression Lab** (Python, pytest, GitHub Actions)

- Built a pytest regression suite (28 test cases across 12 scenarios) that drives the real NXP
  SPSDK 3.13.0 `nxpcrypto` CLI to validate ECDSA P-256 key generation, firmware signing, signature
  verification and SHA-256 digests.
- Designed security-negative tests (tampered firmware, wrong public key, corrupted and truncated
  signatures, malformed keys) with positive controls and an independent oracle (Python
  `cryptography`/`hashlib`) to prevent false-positive results.
- Set up CI/CD with GitHub Actions (Ruff, pytest, JUnit report artifact), and showed through
  deliberate harness mutations that the suite detects regressions.

## C. Short application paragraph

I built a small project to learn what security software testing looks like in practice. It is a
pytest suite that runs the real `nxpcrypto` tool from NXP's open-source SPSDK. It checks that
valid firmware signatures verify and that tampered firmware, wrong keys or damaged signatures are
rejected, and it cross-checks the results with Python's `cryptography` library. While doing this
I found that the verify command returns exit code 0 even for an invalid signature, which taught
me why a negative test has to prove that the check actually ran. I would like to keep learning
this kind of careful validation work in the Security Software Test Engineering internship.

## D. LinkedIn project description

**SPSDK Security Regression Lab**: an independent, hardware-free test suite for the cryptographic
command-line tools in NXP's open-source Secure Provisioning SDK. It signs and verifies synthetic
firmware with ECDSA P-256, checks SHA-256 digests, and feeds the tool invalid inputs (tampered
firmware, wrong keys, corrupted signatures) to confirm they are rejected. An independent Python
`cryptography` oracle cross-checks the results, and GitHub Actions runs Ruff and pytest on every
change. This is a personal learning project, not affiliated with NXP.

## E. Interview elevator pitch (about 60 seconds)

"Secure boot depends on signing tools that accept good firmware and reject anything modified. I
wanted to practise testing that, so I wrote a pytest suite around the real `nxpcrypto` CLI from
NXP's SPSDK. The suite generates P-256 keys, signs a synthetic firmware file and verifies it. Then
the negative tests change one thing at a time: a byte of the firmware, the public key, or the
signature. Each one must be rejected. One thing I learned is that the verify command returns
exit code 0 even when the signature is wrong. So my harness reads the actual verdict, runs a
positive control first, and treats setup errors as failures instead of 'successful rejections'.
I also verify every SPSDK signature independently with Python's `cryptography` library, so the
tool isn't only checking itself. Everything runs in GitHub Actions. To be sure the tests are
meaningful, I broke the harness on purpose and checked that seven tests failed. The main
limitation is that it's all host-side: there's no MCU or boot ROM involved."
