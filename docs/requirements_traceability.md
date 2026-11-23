# Requirements traceability

This table maps skills relevant to a security software test engineering role to what this
repository actually implements. It is deliberately conservative.

| Internship skill | Our implementation | Verification evidence | Limitations |
|---|---|---|---|
| Python automation | `cli_runner.py` drives the real `nxpcrypto` executable through `subprocess` with timeouts and captured output | 28 integration tests execute it; see [test_plan.md](test_plan.md) | Wraps one CLI tool only |
| Automated testing with pytest | Fixtures in `conftest.py`, parametrized tests, a custom `negative` marker, JUnit XML output | Local run: 28 passed, 0 skipped; CI run on GitHub Actions | No coverage measurement |
| Security / negative testing | Tampered firmware, wrong key, corrupted and truncated signatures, malformed keys, missing files, wrong digest | CRYPTO-004 to 007 and 009 to 011 pass by explicit `REJECTED`/error verdicts | Synthetic inputs, no fuzzing |
| Avoiding false positives | Positive control before each negative test; `ACCEPTED`/`REJECTED`/`ERROR` classifier; harness self-check test | Mutation run: 7 negative tests failed when the classifier accepted everything, and the guard test failed when errors were counted as rejections | Text-based verdicts depend on SPSDK's message wording |
| Cryptography fundamentals | ECDSA P-256/SHA-256 signing and verification, DER encoding, SHA-256 digests | CRYPTO-001, 002, 008 and 012 cross-checked with `cryptography` and `hashlib` | Uses libraries; no cryptography implemented here |
| Independent verification (test oracles) | `oracle.py` verifies SPSDK signatures without calling SPSDK | CRYPTO-002 and CRYPTO-012 | Oracle and SPSDK both use OpenSSL through `cryptography`, so they are not fully independent implementations |
| Embedded software context | Firmware-like binary fixtures, secure-boot style sign/verify flow, NXP tooling | Demo script and CRYPTO-002 to 007 | No MCU, boot ROM or real image formats ([limitations.md](limitations.md)) |
| Debugging | `CommandResult.describe()` and `explain()` name the failure class and show the command, exit code and output | Mutation runs produced `SECURITY FAILURE: invalid input was unexpectedly ACCEPTED` with the raw stdout | Plain text diagnostics, no log files |
| CI/CD | `.github/workflows/ci.yml`: Ruff, pytest, demo, artifact upload on push and PR | GitHub Actions run results on the Actions tab | Single OS (Ubuntu) and a single Python version in CI |
| Code quality | Ruff lint (including bandit-style `S` rules) and format check; type hints; small modules | `ruff check .` and `ruff format --check .` pass locally and in CI | No static type checker run |
| Reading vendor tools and docs | CLI options and behaviour confirmed with `--help` and real runs; the exit-code-0-on-invalid-signature behaviour was documented | [architecture.md](architecture.md) "Observed CLI semantics" | Based on one SPSDK version |
