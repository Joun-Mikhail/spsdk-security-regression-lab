"""Turn raw ``nxpcrypto`` results into explicit verdicts.

Observed behaviour of SPSDK 3.13.0 (verified by running the real CLI):

* ``signature verify`` exits with code **0 for both a valid and an invalid signature**.
  The verdict is only in stdout: ``Signature IS matching the public key.`` versus
  ``Signature IS NOT matching the public key.``  A test that only checked the exit code
  would therefore treat a forged signature as accepted.
* CLI usage errors (missing file, bad option) exit with code 2 and print ``Error:``.
* Library errors (for example an unparsable key) exit with code 2 and print ``SPSDKError``.
* ``digest -c <reference>`` exits 0 with ``Digests are the same.`` or exits 1 with
  ``Digests differ!``.

The classifiers below only report ``REJECTED`` when the tool clearly reached the
cryptographic check and said "no". Anything else is ``ERROR`` so that a broken setup can
never be mistaken for a successful security rejection.
"""

from __future__ import annotations

import re
from enum import Enum

from spsdk_regression.cli_runner import CommandResult

_SIG_ACCEPTED = re.compile(r"^Signature IS matching the public key\.$", re.MULTILINE)
_SIG_REJECTED = re.compile(r"^Signature IS NOT matching the public key\.$", re.MULTILINE)
_DIGEST_LINE = re.compile(
    r"^(?P<alg>[A-Z0-9_-]+)\((?P<file>.+)\)= (?P<hex>[0-9a-f]+)$", re.MULTILINE
)
_DIGEST_SAME = "Digests are the same."
_DIGEST_DIFFER = "Digests differ!"


class Verdict(Enum):
    ACCEPTED = "accepted"  # tool ran the check and accepted the input
    REJECTED = "rejected"  # tool ran the check and rejected the input
    ERROR = "error"  # tool did not reach a verdict (usage error, crash, bad input)


def classify_signature_verify(result: CommandResult) -> Verdict:
    """Classify a ``nxpcrypto signature verify`` result."""
    accepted = bool(_SIG_ACCEPTED.search(result.stdout))
    rejected = bool(_SIG_REJECTED.search(result.stdout))
    if result.returncode != 0 or accepted == rejected:
        return Verdict.ERROR
    return Verdict.ACCEPTED if accepted else Verdict.REJECTED


def classify_digest_compare(result: CommandResult) -> Verdict:
    """Classify a ``nxpcrypto digest -c <reference>`` result."""
    if result.returncode == 0 and _DIGEST_SAME in result.output:
        return Verdict.ACCEPTED
    if result.returncode == 1 and _DIGEST_DIFFER in result.output:
        return Verdict.REJECTED
    return Verdict.ERROR


def parse_digest(result: CommandResult, algorithm: str = "SHA256") -> str:
    """Extract the hex digest from ``nxpcrypto digest`` stdout.

    Only a line of the exact form ``SHA256(<file>)= <hex>`` is accepted; arbitrary output is
    never treated as a digest.
    """
    if result.returncode != 0:
        raise ValueError(f"digest command failed\n{result.describe()}")
    matches = [m for m in _DIGEST_LINE.finditer(result.stdout) if m["alg"] == algorithm.upper()]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one {algorithm} digest line, found {len(matches)}\n"
            f"{result.describe()}"
        )
    return matches[0]["hex"]


def explain(expected: Verdict, actual: Verdict, result: CommandResult) -> str:
    """Assertion message that names the failure class, followed by the raw diagnostics."""
    if actual == expected:
        reason = "OK"
    elif expected is Verdict.REJECTED and actual is Verdict.ACCEPTED:
        reason = "SECURITY FAILURE: invalid input was unexpectedly ACCEPTED"
    elif expected is Verdict.ACCEPTED and actual is Verdict.REJECTED:
        reason = "UNEXPECTED REJECTION: valid input was rejected"
    else:
        reason = "SETUP/HARNESS FAILURE: the tool did not reach a cryptographic verdict"
    return f"{reason} (expected {expected.value}, got {actual.value})\n{result.describe()}"
