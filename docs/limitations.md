# Limitations

This project tests a **host-side command-line tool** with **synthetic data**. Please read the
results with that scope in mind.

- **No physical MCU.** No NXP device is connected or programmed.
- **No hardware secure boot validation.** Boot ROM signature checks, eFuse/OTP key hashes and
  boot images are not exercised.
- **No secure enclave or secure element testing**, for example EdgeLock.
- **No provisioning onto real devices.** No keys or images are written to hardware.
- **No RTOS or firmware execution.** The "firmware" is never run.
- **Synthetic binaries.** Test images are deterministic pseudo-random bytes (1 B to 4 KiB), not
  deployable production firmware or SPSDK container formats (MBI, AHAB, HAB, SB files).
- **Narrow algorithm scope.** Only secp256r1 with SHA-256 and DER encoding is covered. RSA, other
  curves, post-quantum keys, NXP-specific signature encoding, signature regions and
  password-protected keys are not tested.
- **Not a security audit or certification of SPSDK.** Passing tests show that specific expected
  behaviours hold. They do not show the absence of vulnerabilities.
- **Verified environments only.** Executed on Linux x86_64 with Python 3.12.3 and SPSDK 3.13.0
  locally, plus the GitHub Actions `ubuntu-latest` runner with Python 3.12. The code uses
  `pathlib` and looks for `nxpcrypto.exe` on Windows, but **Windows has not been executed** as
  part of this delivery.
- **Output-text dependency.** SPSDK 3.13.0 signals an invalid signature only through stdout text,
  with exit code 0. The classifier therefore matches two exact lines. A future SPSDK version that
  rewords them would cause tests to fail with `ERROR`. That is safe (no false passes) but needs
  maintenance.
