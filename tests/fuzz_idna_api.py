#!/usr/bin/env python3
"""OSS-Fuzz target for the whole-domain and per-label API.

Each input selects an operation and flag combination from its leading bytes
and feeds the remainder as the domain or label. The harness asserts the same
invariants as ``tests/test_idna_properties.py``: only :class:`idna.IDNAError`
may escape, successful output is bounded ASCII, encoding then decoding then
encoding again is stable, and UTS #46 remapping is NFC and idempotent.

OSS-Fuzz builds every ``fuzz_*.py`` it finds in the checkout, so this file
needs no registration there. To run it locally::

    pip install atheris .
    python tests/fuzz_idna_api.py -max_total_time=60

Any libFuzzer flag is accepted; a crash writes a ``crash-*`` file which can be
passed back as an argument to reproduce. ``tests/test_idna_fuzz_targets.py``
smoke-tests this harness in the ordinary test suite without atheris.
"""

import sys
import unicodedata

import atheris  # ty: ignore[unresolved-import]

with atheris.instrument_imports():
    import idna

MAX_INPUT = 1100  # just past idna's 1024-character input cap
STD3_ASCII = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-.")


def _only_idnaerror(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except idna.IDNAError:
        return None


def fuzz_encode(fdp):
    strict, uts46, std3 = fdp.ConsumeBool(), fdp.ConsumeBool(), fdp.ConsumeBool()
    s = fdp.ConsumeUnicode(MAX_INPUT)
    encoded = _only_idnaerror(idna.encode, s, strict=strict, uts46=uts46, std3_rules=std3)
    if encoded is None:
        return
    encoded.decode("ascii")
    assert len(encoded) <= 254, encoded
    for label in encoded.rstrip(b".").split(b"."):
        assert 0 < len(label) <= 63, encoded
    # Anything encode() produced must decode, and re-encode to itself
    # (up to ASCII case, since ulabel() lowercases while alabel() does not).
    decoded = idna.decode(encoded)
    assert idna.encode(decoded) == encoded.lower(), (encoded, decoded)
    assert idna.decode(encoded, display=True) == decoded


def fuzz_decode(fdp):
    strict, uts46, std3, display = fdp.ConsumeBool(), fdp.ConsumeBool(), fdp.ConsumeBool(), fdp.ConsumeBool()
    data = fdp.ConsumeUnicode(MAX_INPUT) if fdp.ConsumeBool() else fdp.ConsumeBytes(MAX_INPUT)
    _only_idnaerror(idna.decode, data, strict=strict, uts46=uts46, std3_rules=std3, display=display)


def fuzz_uts46_remap(fdp):
    std3 = fdp.ConsumeBool()
    s = fdp.ConsumeUnicode(MAX_INPUT)
    out = _only_idnaerror(idna.uts46_remap, s, std3_rules=std3)
    if out is None:
        return
    assert unicodedata.is_normalized("NFC", out), out
    assert idna.uts46_remap(out, std3_rules=std3) == out, out
    if std3:  # UTS #46 §4.1 UseSTD3ASCIIRules
        assert all(c in STD3_ASCII for c in out if c.isascii()), out


def fuzz_labels(fdp):
    label = fdp.ConsumeUnicode(MAX_INPUT)
    for fn in (
        idna.alabel,
        idna.ulabel,
        idna.check_label,
        idna.check_bidi,
        idna.check_hyphen_ok,
        idna.check_initial_combiner,
        idna.check_nfc,
        idna.valid_label_length,
    ):
        _only_idnaerror(fn, label)
    _only_idnaerror(idna.ulabel, label.encode("utf-8", "surrogatepass"))
    _only_idnaerror(idna.check_label, label.encode("utf-8", "surrogatepass"))
    encoded = _only_idnaerror(idna.alabel, label)
    if encoded is not None:
        assert idna.alabel(idna.ulabel(encoded)) == encoded.lower(), (label, encoded)


OPERATIONS = (fuzz_encode, fuzz_decode, fuzz_uts46_remap, fuzz_labels)


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    OPERATIONS[fdp.ConsumeIntInRange(0, len(OPERATIONS) - 1)](fdp)


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
