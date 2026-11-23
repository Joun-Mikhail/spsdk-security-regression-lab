# Interview and learning guide

A plain-language guide to the ideas behind this project. Each concept has a one-line
explanation, an example, why it matters to a chip company, where it appears in this repository,
and a likely interview question.

## If you only have 30 minutes

1. **Digital signatures (ECDSA)**: sign with the private key, verify with the public key.
2. **Tamper detection**: change one byte and verification must fail.
3. **Negative testing and false positives**: a "rejected" result only counts if the check really ran.
4. **Independent test oracle**: check the tool's answer with a different implementation.
5. **CI/CD with GitHub Actions**: every change re-runs Ruff and pytest automatically.

## Signature vs. encryption

- **Encryption** hides data. Only the holder of the right key can read it.
- **A digital signature** does not hide anything. It proves *who* produced the data and that it
  has *not changed*. Anyone can read signed firmware, but only the holder of the private key can
  produce a signature that the public key accepts.
- Secure boot needs signatures, not encryption: the chip must refuse modified code, even if the
  code itself is public.

## Concepts

| # | Concept | One sentence | Simple example | Why it matters to NXP | Where in this repo | Likely question |
|---|---|---|---|---|---|---|
| 1 | Firmware | Software stored in a device's flash that runs on its microcontroller. | The code in a smart thermostat. | NXP MCUs run customer firmware. | `synthetic_firmware()` in `test_data.py` | "What is the difference between firmware and an application?" |
| 2 | Embedded security | Protecting devices so they only run trusted code and keep secrets safe. | A device refusing an unsigned update. | Secure boot and provisioning are core NXP features. | The whole project's scenario | "Why is security harder on embedded devices?" |
| 3 | Digital signature | A value computed from data and a private key that proves origin and integrity. | Signing `firmware.bin` gives `firmware.der`. | Secure boot verifies image signatures. | CRYPTO-002 and 003 | "What does a signature guarantee?" |
| 4 | Public / private keys | A key pair: the private key signs and must stay secret; the public key verifies and can be shared. | `device_key.pem` / `device_key.pub` | The public key (or its hash) is put into the chip; the private key stays with the manufacturer. | CRYPTO-001, `oracle.py` | "What happens if the private key leaks?" |
| 5 | ECDSA | A signature algorithm based on elliptic curves, here the P-256 curve. | `nxpcrypto key generate -k secp256r1` | Small keys and fast verification suit MCUs. | `commands.key_generate` | "Why might ECC be preferred over RSA on an MCU?" |
| 6 | SHA-256 | A hash function that turns any data into a 32-byte fingerprint. | One changed byte gives a completely different hash. | Signatures sign a hash; key hashes are stored in fuses. | CRYPTO-008 and 009 | "Can two files have the same SHA-256?" |
| 7 | Signature verification | Checking a signature with the public key and the data. | `Signature IS matching the public key.` | This is what a boot ROM does before running code. | `classify_signature_verify` | "What three inputs does verification need?" |
| 8 | Tamper detection | Any change to signed data makes verification fail. | Flip byte 0x100, then the result is REJECTED. | It stops modified or malicious firmware. | CRYPTO-004, demo step 6 | "How would you test tamper detection?" |
| 9 | Positive testing | Checking that valid input gives the correct result. | A valid signature is accepted. | A tool that rejects everything is also broken. | CRYPTO-003 | "Why are positive tests needed in security testing?" |
| 10 | Negative testing | Checking that invalid input is refused safely. | Wrong key, truncated signature. | Attackers send invalid input. | `@pytest.mark.negative` tests | "Give three negative tests for a signing tool." |
| 11 | Regression testing | Re-running tests after every change to catch things that broke. | CI on every push. | Tools like SPSDK change often. | CI workflow, mutation demo | "How do you know your tests catch regressions?" |
| 12 | pytest fixtures | Reusable setup functions that pytest injects into tests. | The `signed_firmware` fixture. | They keep many tests short and isolated. | `tests/conftest.py` | "What is `tmp_path` and why use it?" |
| 13 | Parametrized tests | One test function run with several inputs. | Sizes 1, 256 and 4096 bytes. | Wider coverage without copied code. | CRYPTO-002, 004, 008 | "When would you not parametrize?" |
| 14 | CLI automation | Running command-line tools from code and checking their results. | `run_nxpcrypto([...])` | SPSDK is mostly used through CLIs. | `cli_runner.py` | "How do you test a CLI tool?" |
| 15 | subprocess | Python's module for running other programs. | `subprocess.run(cmd, capture_output=True, timeout=60)` | Safe automation of vendor tools. | `run_nxpcrypto` | "Why avoid `shell=True`?" (shell injection) |
| 16 | CI/CD | Automatically building and testing every change. | A push triggers lint and tests. | It catches problems before a release. | `.github/workflows/ci.yml` | "What should fail a CI pipeline?" |
| 17 | GitHub Actions | GitHub's CI service, configured with YAML workflows. | The `regression` job on `ubuntu-latest`. | A common, reproducible test infrastructure. | `ci.yml` | "How do you keep test reports when tests fail?" (`if: always()`) |
| 18 | Independent test oracle | A second, separate way to compute the expected answer. | `cryptography` re-verifies SPSDK's signature. | It stops a tool from "agreeing with itself". | `oracle.py`, CRYPTO-012 | "Why not just use SPSDK's own verify?" |
| 19 | Debugging security failures | Separating "the check rejected it" from "the test setup was broken". | Exit code 2 with `Error:` is classified as ERROR, not REJECTED. | Avoids false confidence. | `diagnostics.py`, `explain()` | "A negative test passes. How do you know it really tested something?" |
| 20 | Limits of hardware-free testing | Host-side tests cannot prove what the chip does at boot. | No boot ROM, no fuses. | It shows honest understanding of scope. | `docs/limitations.md` | "What would you add with real hardware?" |

## Key finding to be able to explain

`nxpcrypto signature verify` in SPSDK 3.13.0 returns **exit code 0 even for an invalid
signature**. Only the printed text says `IS NOT matching`. If a test checked only the exit code,
a forged signature would look valid. That is why this project classifies the output text, runs a
positive control first, and has a guard test so that errors are never counted as rejections.

## 10 practice questions

1. **What does this project test?** The `nxpcrypto` CLI from NXP SPSDK. It checks that valid ECDSA
   P-256 signatures and SHA-256 digests are correct, and that tampered or invalid inputs are
   rejected.
2. **Why is it "hardware-free"?** It tests the host-side signing tools with synthetic files, so it
   runs anywhere, including CI. It does not test what the chip does.
3. **How does a tamper test work?** Sign the firmware, check that verification passes (positive
   control), change one byte, verify again, and require the explicit "NOT matching" verdict.
4. **Why the positive control?** It proves that the command, paths and keys are right. Then the
   rejection can only come from the byte I changed.
5. **What is a false positive in a negative test?** The test passes because something else broke,
   for example a missing file. My classifier reports that as ERROR, and the test fails.
6. **Why use an independent oracle?** If SPSDK both signs and verifies, a bug could cancel itself
   out. The `cryptography` package checks the signature separately.
7. **Why not compare signatures byte by byte?** ECDSA uses a random value, so two valid signatures
   of the same data differ.
8. **How is `subprocess` used safely?** With argument lists and no `shell=True`, a timeout, captured
   output, and no secrets on the command line.
9. **How did you show the tests catch regressions?** I broke the classifier on purpose. 7 negative
   tests failed and pytest returned 1. Then I reverted the change and all 28 passed.
10. **What are the limitations?** There is no MCU, boot ROM, real image format or provisioning,
    only P-256/SHA-256, and it was verified only on SPSDK 3.13.0 on Linux.
