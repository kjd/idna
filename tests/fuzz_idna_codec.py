#!/usr/bin/env python3
"""OSS-Fuzz target for the ``idna2008`` codec.

Exercises the one-shot codec and, more importantly, the incremental
encoder/decoder: the input is fed in fuzzer-chosen chunk sizes and the
concatenated result must equal the one-shot result (or both must raise
:class:`idna.IDNAError`). The buffering logic in
:mod:`idna.codec` is stateful across calls, which is exactly the kind of
code a fuzzer is good at breaking.

OSS-Fuzz builds every ``fuzz_*.py`` it finds in the checkout, so this file
needs no registration there. To run it locally::

    pip install atheris .
    python tests/fuzz_idna_codec.py -max_total_time=60

Any libFuzzer flag is accepted; a crash writes a ``crash-*`` file which can be
passed back as an argument to reproduce. ``tests/test_idna_fuzz_targets.py``
smoke-tests this harness in the ordinary test suite without atheris.
"""

import codecs
import sys

import atheris  # ty: ignore[unresolved-import]

with atheris.instrument_imports():
    import idna
    import idna.codec  # registers the "idna2008" codec

MAX_INPUT = 1100  # just past idna's 1024-character input cap
MAX_CHUNKS = 8


def _outcome(fn, *args):
    try:
        return fn(*args), None
    except idna.IDNAError as err:
        return None, err


def _chunks(fdp, data):
    cuts = sorted(fdp.ConsumeIntInRange(0, len(data)) for _ in range(fdp.ConsumeIntInRange(0, MAX_CHUNKS)))
    points = [0, *cuts, len(data)]
    return [data[i:j] for i, j in zip(points, points[1:])]


def fuzz_encoder(fdp):
    s = fdp.ConsumeUnicode(MAX_INPUT)
    if not s:
        return  # the codec maps "" to b"" by design; core raises "Empty domain"
    one_shot = _outcome(idna.encode, s)
    assert _outcome(s.encode, "idna2008") == one_shot or one_shot[1] is not None

    chunks = _chunks(fdp, s)
    encoder = codecs.getincrementalencoder("idna2008")()

    def incremental():
        out = b"".join(encoder.encode(chunk) for chunk in chunks)
        return out + encoder.encode("", final=True)

    result = _outcome(incremental)
    assert (result[1] is None) == (one_shot[1] is None), (s, chunks, one_shot, result)
    assert result[0] == one_shot[0], (s, chunks, one_shot, result)


def fuzz_decoder(fdp):
    b = fdp.ConsumeBytes(MAX_INPUT)
    if not b:
        return
    one_shot = _outcome(idna.decode, b)
    assert _outcome(b.decode, "idna2008") == one_shot or one_shot[1] is not None

    chunks = _chunks(fdp, b)
    decoder = codecs.getincrementaldecoder("idna2008")()

    def incremental():
        out = "".join(decoder.decode(chunk) for chunk in chunks)
        return out + decoder.decode(b"", final=True)

    result = _outcome(incremental)
    assert (result[1] is None) == (one_shot[1] is None), (b, chunks, one_shot, result)
    assert result[0] == one_shot[0], (b, chunks, one_shot, result)


def fuzz_stream(fdp):
    # StreamWriter/StreamReader wrap the one-shot codec; make sure they only
    # ever raise IDNAError.
    import io

    if fdp.ConsumeBool():
        writer = codecs.getwriter("idna2008")(io.BytesIO())
        _outcome(writer.write, fdp.ConsumeUnicode(MAX_INPUT))
    else:
        reader = codecs.getreader("idna2008")(io.BytesIO(fdp.ConsumeBytes(MAX_INPUT)))
        _outcome(reader.read)


OPERATIONS = (fuzz_encoder, fuzz_decoder, fuzz_stream)


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    OPERATIONS[fdp.ConsumeIntInRange(0, len(OPERATIONS) - 1)](fdp)


def main():
    atheris.Setup(sys.argv, TestOneInput, enable_python_coverage=True)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
