# idna-data

The IDNA and UTS 46 functionality in this library relies upon
pre-calculated lookup tables for performance. These tables are derived
from computing against eligibility criteria in the respective standards
using the command-line script `idna-data` in this directory.

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

## Supplemental Information

While this package does not include data files and/or software from
the Unicode standard, in operating the `idna-data` tool it will retrieve
data files to process that are governed by
[these terms](https://www.unicode.org/license.txt).
