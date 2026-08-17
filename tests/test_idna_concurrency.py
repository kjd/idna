"""Concurrent use of the public API from many threads.

The library keeps no mutable module-level state (the lookup tables are
read-only and ``uts46data`` is imported lazily under the import lock), so
calling it from several threads at once must give exactly the results of
calling it serially. This holds the library to that on every build, and
on free-threaded CPython additionally checks that the GIL really is off
when the environment asked for it, so that a dependency or extension
silently re-enabling it would be noticed.
"""

import codecs
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

import idna
import idna.codec  # registers the idna2008 codec

# A mix of paths: plain ASCII, U-labels, UTS #46 mapping, A-label decoding,
# the codec, and inputs that must fail with a specific error code.
_INPUTS = [
    "example.com",
    "пример.рф",
    "παράδειγμα.δοκιμή",
    "उदाहरण.परीक्षा",
    "例え.テスト",
    "Bücher.Example",
    "xn--e1afmkfd.xn--p1ai",
    "xn--zckzah.xn--zckzah",
    "xn---bbk.example",
    "-bad.example",
    "a\u200cb.example",
    "a" * 64 + ".example",
]


def _outcome(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except idna.IDNAError as err:
        return ("error", err.code)


def _work(rounds: int) -> list:
    """Exercise the API ``rounds`` times and return every outcome, in order."""
    results = []
    for _ in range(rounds):
        for s in _INPUTS:
            results.append(_outcome(idna.encode, s))
            results.append(_outcome(idna.encode, s, uts46=True))
            results.append(_outcome(idna.decode, s))
            results.append(_outcome(idna.decode, s, display=True))
            results.append(_outcome(idna.uts46_remap, s))
            results.append(_outcome(codecs.encode, s, "idna2008"))
    return results


class ConcurrencyTests(unittest.TestCase):
    def test_threads_agree_with_serial_execution(self):
        expected = _work(1)
        with ThreadPoolExecutor(max_workers=8) as pool:
            for outcome in pool.map(lambda _: _work(20), range(16)):
                self.assertEqual(outcome, expected * 20)

    @unittest.skipUnless(
        os.environ.get("PYTHON_GIL") == "0" and hasattr(sys, "_is_gil_enabled"),
        "only meaningful when PYTHON_GIL=0 is set on a free-threaded build",
    )
    def test_gil_stays_disabled_when_requested(self):
        self.assertFalse(sys._is_gil_enabled())


if __name__ == "__main__":
    unittest.main()
