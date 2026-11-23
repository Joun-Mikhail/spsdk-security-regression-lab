"""Independent verification oracle built on the Python ``cryptography`` package.

None of this code calls SPSDK, so it can cross-check SPSDK's outputs.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature


def load_public_key(path: Path) -> ec.EllipticCurvePublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, ec.EllipticCurvePublicKey):
        raise TypeError(f"{path.name} is not an EC public key")
    return key


def load_private_key(path: Path) -> ec.EllipticCurvePrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey):
        raise TypeError(f"{path.name} is not an EC private key")
    return key


def public_keys_equal(a: ec.EllipticCurvePublicKey, b: ec.EllipticCurvePublicKey) -> bool:
    fmt = serialization.PublicFormat.SubjectPublicKeyInfo
    enc = serialization.Encoding.DER
    return a.public_bytes(enc, fmt) == b.public_bytes(enc, fmt)


def is_der_ecdsa_signature(signature: bytes) -> bool:
    """True if ``signature`` parses as an ASN.1 DER ``SEQUENCE { r INTEGER, s INTEGER }``."""
    try:
        r, s = decode_dss_signature(signature)
    except ValueError:
        return False
    return r > 0 and s > 0


def ecdsa_sha256_verify(public_key_path: Path, data: bytes, der_signature: bytes) -> bool:
    """Verify a DER ECDSA/SHA-256 signature independently of SPSDK."""
    key = load_public_key(public_key_path)
    try:
        key.verify(der_signature, data, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        return False
    return True
