"""CRYPTO-008 and CRYPTO-009: SHA-256 digest calculation and comparison."""

from __future__ import annotations

import pytest

from spsdk_regression import commands
from spsdk_regression.diagnostics import Verdict, classify_digest_compare, explain, parse_digest
from spsdk_regression.test_data import (
    FIRMWARE_SIZES,
    corrupt_hex_digit,
    sha256_hex,
    synthetic_firmware,
    write_bytes,
)


@pytest.mark.parametrize("size", [0, *FIRMWARE_SIZES], ids=lambda s: f"{s}B")
def test_crypto_008_sha256_matches_hashlib(tmp_path, size):
    """REQ: nxpcrypto's SHA-256 output must equal Python hashlib's digest of the same bytes."""
    data = synthetic_firmware(size, seed=size)
    fw = write_bytes(tmp_path / f"fw_{size}.bin", data)

    result = commands.digest(fw)

    assert parse_digest(result) == sha256_hex(data), result.describe()


@pytest.mark.negative
@pytest.mark.parametrize("position", [0, 63], ids=["first-char", "last-char"])
def test_crypto_009_wrong_reference_digest_is_detected(firmware, position):
    """REQ: ``digest -c`` must report a mismatch when one hex character of the reference differs.

    Positive control first: the correct reference digest must be reported as identical.
    """
    correct = sha256_hex(firmware.read_bytes())
    control = commands.digest(firmware, compare=correct)
    assert classify_digest_compare(control) is Verdict.ACCEPTED, explain(
        Verdict.ACCEPTED, classify_digest_compare(control), control
    )

    wrong = corrupt_hex_digit(correct, position)
    assert wrong != correct
    assert len(wrong) == len(correct)
    result = commands.digest(firmware, compare=wrong)

    actual = classify_digest_compare(result)
    assert actual is Verdict.REJECTED, explain(Verdict.REJECTED, actual, result)
