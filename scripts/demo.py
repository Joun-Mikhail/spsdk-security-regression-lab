"""End-to-end demonstration using the real NXP SPSDK ``nxpcrypto`` CLI.

Every ACCEPTED/REJECTED word printed here comes from classifying real command output; nothing
is hardcoded. The script exits non-zero if any step does not behave as expected.

Run:  python scripts/demo.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from spsdk_regression import commands, oracle
from spsdk_regression.cli_runner import CommandResult, HarnessError
from spsdk_regression.diagnostics import Verdict, classify_signature_verify
from spsdk_regression.test_data import flip_byte, synthetic_firmware, write_bytes


class DemoFailure(Exception):
    pass


def require_ok(result: CommandResult, what: str) -> None:
    if result.returncode != 0:
        raise DemoFailure(f"{what} failed\n{result.describe()}")


def verify(public_key: Path, firmware: Path, signature: Path) -> Verdict:
    return classify_signature_verify(commands.signature_verify(public_key, firmware, signature))


def run(workdir: Path) -> None:
    print("[1] Generating ECC P-256 (secp256r1) test keys with nxpcrypto...")
    private = workdir / "demo_key.pem"
    require_ok(commands.key_generate(private), "key generation")
    public = commands.public_key_path(private)

    print("[2] Creating 4 KiB synthetic firmware image...")
    firmware = write_bytes(workdir / "firmware.bin", synthetic_firmware(4096))

    print("[3] Signing firmware (ECDSA, SHA-256, DER)...")
    signature = workdir / "firmware.der"
    require_ok(commands.signature_create(private, firmware, signature), "signing")
    print(f"    signature: {signature.stat().st_size} bytes")

    original = verify(public, firmware, signature)
    print(f"[4] Verifying original firmware with SPSDK... {original.name}")

    print("[5] Modifying one byte of the firmware (offset 0x100)...")
    tampered = write_bytes(workdir / "tampered.bin", flip_byte(firmware.read_bytes(), 0x100))

    modified = verify(public, tampered, signature)
    print(f"[6] Verifying modified firmware with SPSDK... {modified.name}")

    sig_bytes = signature.read_bytes()
    oracle_ok = oracle.ecdsa_sha256_verify(public, firmware.read_bytes(), sig_bytes)
    oracle_tampered = oracle.ecdsa_sha256_verify(public, tampered.read_bytes(), sig_bytes)
    print(
        "[7] Independent check (Python cryptography): "
        f"original={'ACCEPTED' if oracle_ok else 'REJECTED'}, "
        f"modified={'ACCEPTED' if oracle_tampered else 'REJECTED'}"
    )

    if original is not Verdict.ACCEPTED or not oracle_ok:
        raise DemoFailure(f"valid signature not accepted (SPSDK verdict: {original.name})")
    if modified is not Verdict.REJECTED or oracle_tampered:
        raise DemoFailure(f"tampered firmware not rejected (SPSDK verdict: {modified.name})")


def main() -> int:
    print("SPSDK Security Regression Demonstration\n")
    try:
        with tempfile.TemporaryDirectory(prefix="spsdk-demo-") as tmp:
            run(Path(tmp))
    except (DemoFailure, HarnessError) as exc:
        print(f"\nResult: FAILED - {exc}", file=sys.stderr)
        return 1
    print("\nTemporary keys and files removed.")
    print("Result: valid signature accepted; tampered firmware rejected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
