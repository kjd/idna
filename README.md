# Internationalized Domain Names in Applications (IDNA)

Support for [Internationalized Domain Names in
Applications (IDNA)](https://tools.ietf.org/html/rfc5891)
and [Unicode IDNA Compatibility Processing](https://unicode.org/reports/tr46/).

The latest versions of these standards supplied here provide
more comprehensive language coverage and reduce the potential of
allowing domains with known security vulnerabilities. This library
is a suitable replacement for the "encodings.idna"
module that comes with the Python standard library, but which
only supports an older superseded IDNA specification from 2003.

Basic functions are simply executed:

```pycon
>>> import idna
>>> idna.encode('ドメイン.テスト')
b'xn--eckwd4c7c.xn--zckzah'
>>> print(idna.decode('xn--eckwd4c7c.xn--zckzah'))
ドメイン.テスト
```


## Installation

This package is available for installation from PyPI via the
typical mechanisms, such as:

```bash
$ python3 -m pip install idna
```


## Usage

For typical usage, the `encode` and `decode` functions will take a
domain name argument and perform a conversion to ASCII-compatible encoding
(known as A-labels), or to Unicode strings (known as U-labels)
respectively.

```pycon
>>> import idna
>>> idna.encode('ドメイン.テスト')
b'xn--eckwd4c7c.xn--zckzah'
>>> print(idna.decode('xn--eckwd4c7c.xn--zckzah'))
ドメイン.テスト
```

Conversions can be applied at a per-label basis using the `ulabel` or
`alabel` functions if necessary:

```pycon
>>> idna.alabel('测试')
b'xn--0zwm56d'
```


### Compatibility Mapping (UTS #46)

This library provides support for [Unicode IDNA Compatibility
Processing](https://unicode.org/reports/tr46/) which normalizes input from
different potential ways a user may input a domain prior to performing the IDNA
conversion operations. This functionality, known as a
[mapping](https://tools.ietf.org/html/rfc5895), is considered by the
specification to be a local user-interface issue distinct from IDNA
conversion functionality.

For example, "Königsgäßchen" is not a permissible label as *LATIN
CAPITAL LETTER K* is not allowed (nor are capital letters in general).
UTS 46 will convert this into lower case prior to applying the IDNA
conversion.

```pycon
>>> import idna
>>> idna.encode('Königsgäßchen')
...
idna.core.InvalidCodepoint: Codepoint U+004B at position 1 of 'Königsgäßchen' not allowed
>>> idna.encode('Königsgäßchen', uts46=True)
b'xn--knigsgchen-b4a3dun'
>>> print(idna.decode('xn--knigsgchen-b4a3dun'))
königsgäßchen
```


## Command-line tool

The package supports command-line usage to convert domain names
between their Unicode and ASCII-compatible forms. It can be run either
as a module (`python3 -m idna`) or, once installed (such as with `uv
tool` or `pipx`), via the `idna` script:

```bash
$ uv tool install idna
$ idna xn--e1afmkfd.xn--p1ai
пример.рф
$ idna пример.рф
xn--e1afmkfd.xn--p1ai
```

With no mode flag the direction is chosen automatically: inputs
containing an `xn--` label are decoded, anything else is encoded. Pass
`-e`/`--encode` or `-d`/`--decode` to force a specific direction.

Multiple domains may be supplied at once, either as positional
arguments or by piping one domain per line on standard input:

```bash
$ idna пример.рф παράδειγμα
xn--e1afmkfd.xn--p1ai
xn--hxajbheg2az3al
$ cat domainlist.txt | idna
```

When more than one domain is supplied without a mode flag, the
direction is picked from the first input and that mode is applied to
every remaining input, so a stream of A-labels all decode and a stream
of U-labels all encode. Pass `-e`/`--encode` or `-d`/`--decode` to
override the heuristic if the first input is ambiguous.

UTS #46 mapping is applied by default, which lets the tool accept
inputs that aren't strictly valid IDNA 2008 — such as uppercase
letters — by normalising them first:

```bash
$ idna ΠΑΡΆΔΕΙΓΜΑ.ΕΛ
xn--hxajbheg2az3al.xn--qxam
```

Pass `--strict` to disable UTS #46 and apply IDNA 2008 rules verbatim;
the same input will then be rejected.

Conversion failures are reported on stderr together with the
offending input; processing continues with the remaining domains and
the tool exits with a non-zero status if any conversion failed.


## Exceptions

All errors raised during the conversion following the specification
should raise an exception derived from the `idna.IDNAError` base
class.

More specific exceptions that may be generated as `idna.IDNABidiError`
when the error reflects an illegal combination of left-to-right and
right-to-left characters in a label; `idna.InvalidCodepoint` when
a specific codepoint is an illegal character in an IDN label (i.e.
INVALID); and `idna.InvalidCodepointContext` when the codepoint is
illegal based on its position in the string (i.e. it is CONTEXTO or CONTEXTJ
but the contextual requirements are not satisfied.)

## Building and Diagnostics

The IDNA and UTS 46 functionality relies upon pre-calculated lookup
tables for performance. These tables are derived from computing against
eligibility criteria in the respective standards using the command-line
script `tools/idna-data`.

This tool will fetch relevant codepoint data from the Unicode repository
and perform the required calculations to identify eligibility. There are
three main modes:

* `idna-data make-libdata`. Generates `idnadata.py` and
  `uts46data.py`, the pre-calculated lookup tables used for IDNA and
  UTS 46 conversions. Implementers who wish to track this library against
  a different Unicode version may use this tool to manually generate a
  different version of the `idnadata.py` and `uts46data.py` files.

* `idna-data make-table`. Generate a table of the IDNA disposition
  (e.g. PVALID, CONTEXTJ, CONTEXTO) in the format found in Appendix
  B.1 of RFC 5892 and the pre-computed tables published by [IANA](https://www.iana.org/).

* `idna-data U+0061`. Prints debugging output on the various
  properties associated with an individual Unicode codepoint (in this
  case, U+0061), that are used to assess the IDNA and UTS 46 status of a
  codepoint. This is helpful in debugging or analysis.

The tool accepts a number of arguments, described using `idna-data -h`.
Most notably, the `--version` argument allows the specification
of the version of Unicode to be used in computing the table data. For
example, `idna-data --version 9.0.0 make-libdata` will generate
library data against Unicode 9.0.0.


## Additional Notes

* **Packages**. The latest tagged release version is published in the
  [Python Package Index](https://pypi.org/project/idna/).

* **Version support**. This library supports Python 3.9 and higher.
  As this library serves as a low-level toolkit for a variety of
  applications, we strive to support all versions of Python that are
  not beyond end-of-life.

* **Testing**. The library has a test suite based on each rule of the
  IDNA specification, as well as tests that are provided as part of the
  Unicode Technical Standard 46, [Unicode IDNA Compatibility Processing](https://unicode.org/reports/tr46/).

* **Emoji**. It is an occasional request to support emoji domains in
  this library. Encoding of symbols like emoji is expressly prohibited by
  the IDNA technical standard, and emoji domains are broadly phased
  out across the domain industry due to associated security risks.

* **Transitional processing**. Unicode 16.0.0 removed transitional
  processing so the `transitional` argument for the encode() method
  no longer has any effect and will be removed at a later date.
