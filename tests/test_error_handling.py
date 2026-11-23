"""CRYPTO-010 and CRYPTO-011: invalid inputs, plus self-checks of the harness classifiers."""

from __future__ import annotations

import pytest

from spsdk_regression import commands
from spsdk_regression.diagnostics import Verdict, classify_signature_verify


@pytest.mark.negative
@pytest.mark.parametrize(
    "content",
    [
        b"this is not a key\n",
        b"",
        b"-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----\n",
    ],
    ids=["text", "empty-file", "bad-pem-body"],
)
def test_crypto_010_malformed_private_key_is_refused(tmp_path, firmware, keypair, content):
    """REQ: signing with an unparsable key must fail cleanly and produce no signature file.

    Positive control: the same command with a valid key succeeds, so the failure below is caused
    by the key content and not by a wrong option or path.
    """
    control_sig = tmp_path / "control.der"
    assert commands.signature_create(keypair.private, firmware, control_sig).returncode == 0

    bad_key = tmp_path / "malformed.pem"
    bad_key.write_bytes(content)
    out = tmp_path / "should_not_exist.der"

    result = commands.signature_create(bad_key, firmware, out)

    assert result.returncode != 0, f"malformed key was accepted\n{result.describe()}"
    assert "SPSDKError" in result.output, result.describe()  # library error, not a usage error
    assert "Traceback" not in result.output, "unhandled Python exception\n" + result.describe()
    assert not out.exists(), "a signature artefact was written despite the failure"


@pytest.mark.negative
def test_crypto_011_missing_firmware_sign_fails_without_artifact(tmp_path, keypair):
    """REQ: signing a nonexistent file must fail with an error and leave no output file."""
    missing = tmp_path / "does_not_exist.bin"
    out = tmp_path / "out.der"

    result = commands.signature_create(keypair.private, missing, out)

    assert result.returncode != 0, result.describe()
    assert "not found" in result.output.lower(), result.describe()
    assert "signed" not in result.stdout.lower(), "CLI claimed success\n" + result.describe()
    assert not out.exists()


@pytest.mark.negative
def test_crypto_011_missing_firmware_digest_fails(tmp_path):
    """REQ: hashing a nonexistent file must fail and print no digest."""
    result = commands.digest(tmp_path / "does_not_exist.bin")

    assert result.returncode != 0, result.describe()
    assert "does not exist" in result.output, result.describe()
    assert "SHA256(" not in result.stdout, result.describe()


@pytest.mark.negative
def test_harness_never_counts_usage_errors_as_rejections(tmp_path, signed_firmware):
    """False-positive guard: a verification that cannot run (missing public key) must be
    classified as ERROR, not as a successful security REJECTED verdict."""
    result = commands.signature_verify(
        tmp_path / "missing.pub", signed_firmware.firmware, signed_firmware.signature
    )
    assert result.returncode != 0, result.describe()
    assert classify_signature_verify(result) is Verdict.ERROR, result.describe()
