"""Shared pytest fixtures.

Every fixture writes into pytest's per-test ``tmp_path``, so tests are independent, need no
particular execution order, and leave no key material behind in the repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from spsdk_regression import TESTED_SPSDK_VERSION, commands
from spsdk_regression.cli_runner import locate_nxpcrypto, run_nxpcrypto
from spsdk_regression.test_data import synthetic_firmware, write_bytes


@dataclass(frozen=True)
class KeyPair:
    private: Path
    public: Path


@dataclass(frozen=True)
class SignedFirmware:
    keys: KeyPair
    firmware: Path
    signature: Path


def pytest_report_header(config: pytest.Config) -> list[str]:
    try:
        version = run_nxpcrypto(["--version"]).stdout.strip()
    except Exception as exc:  # report header must never crash the session
        version = f"unavailable ({exc})"
    return [f"nxpcrypto: {version} (suite verified against SPSDK {TESTED_SPSDK_VERSION})"]


@pytest.fixture(scope="session", autouse=True)
def nxpcrypto_available() -> Path:
    """Fail fast (as an error, never as a pass) if the tool under test is missing."""
    exe = locate_nxpcrypto()
    result = run_nxpcrypto(["--version"], executable=exe)
    assert result.returncode == 0, result.describe()
    return exe


@pytest.fixture
def make_keypair(tmp_path: Path):
    """Factory: generate a fresh secp256r1 key pair with the real ``nxpcrypto``."""

    def _make(name: str = "device_key", key_type: str = "secp256r1") -> KeyPair:
        private = tmp_path / f"{name}.pem"
        result = commands.key_generate(private, key_type)
        public = commands.public_key_path(private)
        assert result.returncode == 0, f"key generation failed\n{result.describe()}"
        assert private.is_file(), result.describe()
        assert public.is_file(), result.describe()
        return KeyPair(private=private, public=public)

    return _make


@pytest.fixture
def keypair(make_keypair) -> KeyPair:
    return make_keypair("device_key")


@pytest.fixture
def unrelated_keypair(make_keypair) -> KeyPair:
    return make_keypair("unrelated_key")


@pytest.fixture
def firmware(tmp_path: Path) -> Path:
    """4 KiB deterministic synthetic firmware image."""
    return write_bytes(tmp_path / "firmware.bin", synthetic_firmware(4096))


@pytest.fixture
def signed_firmware(tmp_path: Path, keypair: KeyPair, firmware: Path) -> SignedFirmware:
    """Firmware plus a DER signature created by SPSDK with ``keypair``."""
    signature = tmp_path / "firmware.sig.der"
    result = commands.signature_create(keypair.private, firmware, signature)
    assert result.returncode == 0, f"signing failed\n{result.describe()}"
    assert signature.is_file(), result.describe()
    assert signature.stat().st_size > 0, result.describe()
    return SignedFirmware(keys=keypair, firmware=firmware, signature=signature)
