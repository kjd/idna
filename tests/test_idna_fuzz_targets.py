"""Smoke-test the OSS-Fuzz harnesses (``tests/fuzz_*.py``) without libFuzzer.

The real fuzzers need ``atheris`` (and a libFuzzer-capable clang) to run.
Here a minimal stand-in for the parts of ``atheris`` the harnesses use is
installed into ``sys.modules`` and each ``TestOneInput`` is driven with
pseudo-random bytes. This catches harnesses that fall out of step with the
library API long before OSS-Fuzz reports a build or run failure.
"""

from __future__ import annotations

import contextlib
import importlib.util
import random
import sys
import types
import unittest
from pathlib import Path
from typing import Any, Callable
from unittest import mock

TARGETS = sorted(Path(__file__).resolve().parent.glob("fuzz_*.py"))
ITERATIONS = 2000

# Well-formed inputs are vanishingly rare in random bytes, so half the
# iterations splice one of these behind a random header to reach the
# harnesses' success-path assertions (round trips, idempotence, ...).
SEEDS = [
    b"example.com",
    b"ExAmPlE.COM.",
    b"a-b.c1.d",
    "пример.рф".encode(),
    b"xn--e1afmkfd.xn--p1ai",
    "παράδειγμα.δοκιμή".encode(),
    "उदाहरण.परीक्षा".encode(),
    "例え.テスト".encode(),
    "bücher.example".encode(),
    "Faß.de".encode(),
    "a\u200cb.example".encode(),
    b"xn--.example",
    b"-hyphen.example",
    b"xn--80ak6aa92e.com",
    b"xn---bbk.example",  # non-canonical spelling of xn--bbk
    b"XN--MNCHEN-3YA.example",
    b"a." * 200,  # every label valid, but past the 253-octet domain limit
    ("\ufdfa" * 100).encode(),  # UTS #46 maps each to 18 characters, past the input cap
]


class _FuzzedDataProvider:
    """Just enough of ``atheris.FuzzedDataProvider`` for the harnesses."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    def _take(self, n: int) -> bytes:
        chunk = self._data[self._pos : self._pos + n]
        self._pos += len(chunk)
        return chunk

    def ConsumeBool(self) -> bool:
        return bool(self._take(1)[0] & 1) if self._pos < len(self._data) else False

    def ConsumeIntInRange(self, low: int, high: int) -> int:
        raw = self._take(4)
        return low + (int.from_bytes(raw, "little") % (high - low + 1)) if raw else low

    def ConsumeBytes(self, count: int) -> bytes:
        return self._take(count)

    def ConsumeUnicode(self, count: int) -> str:
        return self._take(count).decode("utf-8", "surrogatepass" if self.ConsumeBool() else "replace")


def _fake_atheris() -> types.ModuleType:
    module = types.ModuleType("atheris")
    module.__dict__.update(
        FuzzedDataProvider=_FuzzedDataProvider,
        instrument_imports=contextlib.nullcontext,
        Setup=lambda *args, **kwargs: None,
        Fuzz=lambda *args, **kwargs: None,
    )
    return module


def _load(path: Path) -> Callable[[bytes], Any]:
    with mock.patch.dict(sys.modules, {"atheris": _fake_atheris()}):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.TestOneInput  # type: ignore[no-any-return]


class FuzzTargetSmokeTests(unittest.TestCase):
    def test_targets_survive_random_input(self) -> None:
        rng = random.Random(0)
        for path in TARGETS:
            with self.subTest(target=path.name):
                test_one_input = _load(path)
                for i in range(ITERATIONS):
                    data = rng.randbytes(rng.randrange(0, 200))
                    if i % 2:
                        data = rng.randbytes(rng.randrange(4, 12)) + rng.choice(SEEDS)
                    test_one_input(data)


if __name__ == "__main__":
    unittest.main()
