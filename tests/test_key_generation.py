"""CRYPTO-001: ECC key generation."""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric import ec

from spsdk_regression import commands, oracle


def test_crypto_001_generated_p256_keypair_is_valid_and_matching(keypair):
    """REQ: nxpcrypto must create a loadable secp256r1 private/public key pair that belong together.

    Oracle: the Python cryptography package loads both files independently, checks the curve,
    and checks that the public key derived from the private key equals the written public key.
    """
    private = oracle.load_private_key(keypair.private)
    public = oracle.load_public_key(keypair.public)

    assert isinstance(private.curve, ec.SECP256R1)
    assert isinstance(public.curve, ec.SECP256R1)
    assert private.key_size == 256
    assert oracle.public_keys_equal(private.public_key(), public), (
        "public key written by nxpcrypto does not correspond to the private key"
    )

    # Cross-check with SPSDK's own pairing check as well.
    result = commands.key_verify(keypair.private, keypair.public)
    assert result.returncode == 0, result.describe()


def test_crypto_001b_two_generated_keys_are_distinct(keypair, unrelated_keypair):
    """REQ: two key generations must not produce the same key (fresh randomness each time).

    Also proves the "unrelated key" fixture used by CRYPTO-005 really is a different, valid key.
    """
    a = oracle.load_public_key(keypair.public)
    b = oracle.load_public_key(unrelated_keypair.public)
    assert not oracle.public_keys_equal(a, b)

    result = commands.key_verify(keypair.private, unrelated_keypair.public)
    assert result.returncode != 0, (
        f"SPSDK reported unrelated keys as a valid pair\n{result.describe()}"
    )
    assert "NOT a valid pair" in result.output, result.describe()
