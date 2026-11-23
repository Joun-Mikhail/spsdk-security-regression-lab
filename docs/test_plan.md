# Test plan

**System under test:** `nxpcrypto` CLI from NXP SPSDK 3.13.0 (PyPI), host-side only.
**Algorithms in scope:** ECC secp256r1 (P-256), ECDSA with SHA-256, DER signature encoding, SHA-256 digest.
**Test level:** CLI integration tests with an independent oracle.

## Planned tests

| ID | Objective | Setup | Action | Expected outcome | Requirement |
|---|---|---|---|---|---|
| CRYPTO-001 | Key generation produces a correct P-256 pair | empty `tmp_path` | `key generate -k secp256r1 -o key.pem` | exit 0; `key.pem` and `key.pub` exist; both load in `cryptography`; curve secp256r1; derived public key equals `key.pub`; `key verify` exit 0. A second key differs and `key verify` reports "NOT a valid pair". | Key generation, key relationship |
| CRYPTO-002 | Signing produces a valid DER signature | key pair; firmware of 1, 256 and 4096 bytes | `signature create -a sha256 -e der` | exit 0; non-empty file; parses as DER `SEQUENCE{r,s}`; the oracle verifies it | File signing |
| CRYPTO-003 | A valid signature is accepted | signed 4 KiB firmware | `signature verify` | `Signature IS matching` (verdict `ACCEPTED`) | Signature verification |
| CRYPTO-004 | Firmware tampering is detected | signed firmware; positive control passes | flip 1 byte (offset 0, 2048 or last); verify | verdict `REJECTED` | Firmware integrity |
| CRYPTO-005 | A wrong public key is rejected | signed firmware; an unrelated valid P-256 key; positive control passes | verify with the unrelated key | verdict `REJECTED` | Untrusted keys |
| CRYPTO-006 | A corrupted signature is rejected | signed firmware; positive control passes | XOR one signature byte with 0xFF (last byte, or 10th from the end) | verdict `REJECTED` | Signature corruption |
| CRYPTO-007 | A truncated signature is rejected | signed firmware; positive control passes | keep only the first half of the signature | verdict `REJECTED`, never `ACCEPTED` | Signature corruption |
| CRYPTO-008 | SHA-256 matches an independent implementation | data of 0, 1, 256 and 4096 bytes | `digest -h sha256`, then parse the single `SHA256(<file>)= <hex>` line | equals `hashlib.sha256` | Digest calculation |
| CRYPTO-009 | A wrong reference digest is detected | 4 KiB firmware; positive control `-c <correct>` gives `Digests are the same.` | `-c` with one hex character changed (first or last) | exit 1 with `Digests differ!` (verdict `REJECTED`) | Digest comparison |
| CRYPTO-010 | A malformed key is refused cleanly | positive control signs with a valid key | sign with a text file, an empty file, or a PEM with an invalid body | exit != 0; `SPSDKError`; no Python traceback; no signature file written | Invalid input handling |
| CRYPTO-011 | A missing input file is refused | nonexistent path | `signature create` and `digest` | exit != 0; "not found" or "does not exist"; no success message; no digest printed; no output file | Invalid input handling |
| CRYPTO-012 | Independent verification | SPSDK-signed firmware | `cryptography` ECDSA verify of the original and of a 1-byte-modified copy | original True, modified False | Independent verification |
| EDGE-01 | Empty firmware | empty file | sign, then verify with both SPSDK and the oracle | `ACCEPTED` / True | Edge case |
| EDGE-02 | Paths with spaces and Unicode | `firmware dir ü/image ü.bin`, key `key with space.pem` | sign and verify | `ACCEPTED` | Cross-platform robustness |
| HARNESS-01 | Usage errors are never counted as rejections | missing public key path | `signature verify` | exit != 0 and verdict `ERROR` (not `REJECTED`) | False-positive prevention |

## Executed results

These are actual results, recorded on 2026-11-23 on Linux x86_64 with Python 3.12.3,
SPSDK 3.13.0, cryptography 49.0.0, pytest 9.2.0 and ruff 0.17.6:

| Check | Result |
|---|---|
| Tests collected | 28 |
| Passed / Failed / Skipped / Errors | 28 / 0 / 0 / 0 |
| Duration | ~23-25 s |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 19 files already formatted (Python and Markdown code blocks) |
| `python scripts/demo.py` | exit 0; original `ACCEPTED`, modified `REJECTED` |

The results of the remote CI run are visible on the repository's
[Actions page](https://github.com/Joun-Mikhail/spsdk-security-regression-lab/actions/workflows/ci.yml).
Each run uploads `junit-report` (`reports/junit.xml`) as evidence.

## Regression-detection (mutation) evidence

These changes were made locally to the harness, run, and then reverted. They were never committed.

| Mutation | Tests that failed | What it shows |
|---|---|---|
| `classify_signature_verify` always returns `ACCEPTED` | 7: `test_crypto_004[first/middle/last]`, `test_crypto_005`, `test_crypto_006[last-byte/inside-s]`, `test_crypto_007` (pytest exit code 1). The demo also exited 1. | The negative tests really depend on SPSDK's rejection verdict. A harness that accepted forgeries would be caught. |
| `classify_signature_verify` maps any CLI error to `REJECTED` | 1: `test_harness_never_counts_usage_errors_as_rejections` | A broken setup cannot silently pass as a "successful security rejection". |

After reverting, the full suite passed again with 28 of 28 tests.
