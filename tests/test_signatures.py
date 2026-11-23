"""CRYPTO-002 to CRYPTO-007 and CRYPTO-012: signing, verification and tamper detection.

Pattern used by every negative test (false-positive guard):
  1. positive control: the *same* command with the original inputs must be ACCEPTED, which
     proves paths, options and keys are correct;
  2. change exactly one thing;
  3. require an explicit REJECTED verdict. Usage errors or crashes are classified as ERROR and
     fail the test, so a broken setup can never pass as a "successful rejection".
"""

from __future__ import annotations

import pytest

from spsdk_regression import commands, oracle
from spsdk_regression.diagnostics import Verdict, classify_signature_verify, explain
from spsdk_regression.test_data import FIRMWARE_SIZES, flip_byte, synthetic_firmware, write_bytes


def assert_verdict(expected: Verdict, result) -> None:
    actual = classify_signature_verify(result)
    assert actual is expected, explain(expected, actual, result)


def assert_positive_control(signed) -> None:
    result = commands.signature_verify(signed.keys.public, signed.firmware, signed.signature)
    assert_verdict(Verdict.ACCEPTED, result)


@pytest.mark.parametrize("size", FIRMWARE_SIZES, ids=lambda s: f"{s}B")
def test_crypto_002_signing_produces_valid_der_signature(tmp_path, keypair, size):
    """REQ: nxpcrypto signs firmware of several sizes and emits a well-formed DER ECDSA signature
    that an independent implementation accepts."""
    data = synthetic_firmware(size, seed=size)
    fw = write_bytes(tmp_path / f"fw_{size}.bin", data)
    sig = tmp_path / f"fw_{size}.der"

    result = commands.signature_create(keypair.private, fw, sig)

    assert result.returncode == 0, result.describe()
    signature = sig.read_bytes()
    assert signature, "signature file is empty"
    assert oracle.is_der_ecdsa_signature(signature), f"not DER ECDSA: {signature.hex()}"
    assert oracle.ecdsa_sha256_verify(keypair.public, data, signature)


def test_crypto_003_valid_signature_is_accepted(signed_firmware):
    """REQ: SPSDK explicitly reports a correct signature over unmodified firmware as valid."""
    assert_positive_control(signed_firmware)


@pytest.mark.negative
@pytest.mark.parametrize("index", [0, 2048, -1], ids=["first", "middle", "last"])
def test_crypto_004_tampered_firmware_is_rejected(tmp_path, signed_firmware, index):
    """REQ: changing a single firmware byte after signing must make verification fail."""
    assert_positive_control(signed_firmware)
    original = signed_firmware.firmware.read_bytes()
    tampered = write_bytes(tmp_path / "tampered.bin", flip_byte(original, index))
    assert tampered.read_bytes() != original

    result = commands.signature_verify(
        signed_firmware.keys.public, tampered, signed_firmware.signature
    )
    assert_verdict(Verdict.REJECTED, result)


@pytest.mark.negative
def test_crypto_005_wrong_public_key_is_rejected(signed_firmware, unrelated_keypair):
    """REQ: a signature must not verify under a different, otherwise valid, P-256 public key."""
    assert_positive_control(signed_firmware)
    # Both keys are valid P-256 keys; the only difference is which key is used.
    oracle.load_public_key(unrelated_keypair.public)

    result = commands.signature_verify(
        unrelated_keypair.public, signed_firmware.firmware, signed_firmware.signature
    )
    assert_verdict(Verdict.REJECTED, result)


@pytest.mark.negative
@pytest.mark.parametrize("index", [-1, -10], ids=["last-byte", "inside-s"])
def test_crypto_006_corrupted_signature_is_rejected(tmp_path, signed_firmware, index):
    """REQ: flipping a byte of the signature (firmware and key unchanged) must be rejected."""
    assert_positive_control(signed_firmware)
    corrupted = write_bytes(
        tmp_path / "corrupted.der", flip_byte(signed_firmware.signature.read_bytes(), index, 0xFF)
    )

    result = commands.signature_verify(
        signed_firmware.keys.public, signed_firmware.firmware, corrupted
    )
    assert_verdict(Verdict.REJECTED, result)


@pytest.mark.negative
def test_crypto_007_truncated_signature_is_rejected(tmp_path, signed_firmware):
    """REQ: a shortened signature must never be reported as valid."""
    assert_positive_control(signed_firmware)
    full = signed_firmware.signature.read_bytes()
    truncated = write_bytes(tmp_path / "truncated.der", full[: len(full) // 2])

    result = commands.signature_verify(
        signed_firmware.keys.public, signed_firmware.firmware, truncated
    )
    assert_verdict(Verdict.REJECTED, result)


def test_crypto_012_independent_oracle_agrees_with_spsdk(signed_firmware):
    """REQ: an implementation independent of SPSDK (Python cryptography) must accept the SPSDK
    signature over the original bytes and reject it over modified bytes."""
    data = signed_firmware.firmware.read_bytes()
    signature = signed_firmware.signature.read_bytes()

    assert oracle.ecdsa_sha256_verify(signed_firmware.keys.public, data, signature)
    assert not oracle.ecdsa_sha256_verify(
        signed_firmware.keys.public, flip_byte(data, 0), signature
    )


def test_empty_firmware_round_trip(tmp_path, keypair):
    """Edge case: SPSDK 3.13.0 supports signing an empty file; the result must still verify,
    both in SPSDK and in the independent oracle."""
    empty = write_bytes(tmp_path / "empty.bin", b"")
    sig = tmp_path / "empty.der"

    assert commands.signature_create(keypair.private, empty, sig).returncode == 0
    assert oracle.ecdsa_sha256_verify(keypair.public, b"", sig.read_bytes())
    assert_verdict(Verdict.ACCEPTED, commands.signature_verify(keypair.public, empty, sig))


def test_paths_with_spaces_and_unicode(tmp_path, make_keypair):
    """Edge case: argument-list subprocess calls must handle spaces and non-ASCII paths."""
    workdir = tmp_path / "firmware dir ü"
    workdir.mkdir()
    keys = make_keypair("key with space")
    fw = write_bytes(workdir / "image ü.bin", synthetic_firmware(256))
    sig = workdir / "image ü.der"

    assert commands.signature_create(keys.private, fw, sig).returncode == 0
    assert_verdict(Verdict.ACCEPTED, commands.signature_verify(keys.public, fw, sig))
