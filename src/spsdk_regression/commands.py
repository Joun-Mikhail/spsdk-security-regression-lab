"""Thin, explicit builders for the ``nxpcrypto`` commands exercised by this project.

Each function maps one-to-one to a documented SPSDK 3.13.0 command line, so a reader can see
exactly which real command a test runs. Shared by the pytest suite and ``scripts/demo.py``.
"""

from __future__ import annotations

from pathlib import Path

from spsdk_regression.cli_runner import CommandResult, run_nxpcrypto


def key_generate(private_key: Path, key_type: str = "secp256r1", **kw) -> CommandResult:
    """``nxpcrypto key generate``. SPSDK writes the public key next to it as ``<stem>.pub``."""
    return run_nxpcrypto(["key", "generate", "-k", key_type, "-o", private_key], **kw)


def public_key_path(private_key: Path) -> Path:
    """Location of the public key that ``key generate`` writes (observed: ``<stem>.pub``)."""
    return private_key.with_suffix(".pub")


def key_verify(key1: Path, key2: Path, **kw) -> CommandResult:
    """``nxpcrypto key verify``: do the two keys form a pair / represent the same key?"""
    return run_nxpcrypto(["key", "verify", "-k1", key1, "-k2", key2], **kw)


def signature_create(
    private_key: Path, input_file: Path, output: Path, algorithm: str = "sha256", **kw
) -> CommandResult:
    """``nxpcrypto signature create`` producing a DER-encoded signature."""
    return run_nxpcrypto(
        [
            "signature", "create",
            "-s", private_key,
            "-a", algorithm,
            "-e", "der",
            "-i", input_file,
            "-o", output,
        ],
        **kw,
    )  # fmt: skip


def signature_verify(
    public_key: Path, input_file: Path, signature: Path, algorithm: str = "sha256", **kw
) -> CommandResult:
    """``nxpcrypto signature verify``."""
    return run_nxpcrypto(
        [
            "signature", "verify",
            "-k", public_key,
            "-a", algorithm,
            "-i", input_file,
            "-s", signature,
        ],
        **kw,
    )  # fmt: skip


def digest(
    input_file: Path, algorithm: str = "sha256", compare: str | None = None, **kw
) -> CommandResult:
    """``nxpcrypto digest``, optionally comparing against a reference digest with ``-c``."""
    args: list[str | Path] = ["digest", "-h", algorithm, "-i", input_file]
    if compare is not None:
        args += ["-c", compare]
    return run_nxpcrypto(args, **kw)
