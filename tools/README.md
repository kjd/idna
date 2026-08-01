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

## Supplemental License Information

This package uses data derived from the Unicode Standard, which is
governed by [this license](https://www.unicode.org/license.txt):

UNICODE LICENSE V3

COPYRIGHT AND PERMISSION NOTICE

Copyright © 1991-2026 Unicode, Inc.

NOTICE TO USER: Carefully read the following legal agreement. BY
DOWNLOADING, INSTALLING, COPYING OR OTHERWISE USING DATA FILES, AND/OR
SOFTWARE, YOU UNEQUIVOCALLY ACCEPT, AND AGREE TO BE BOUND BY, ALL OF THE
TERMS AND CONDITIONS OF THIS AGREEMENT. IF YOU DO NOT AGREE, DO NOT
DOWNLOAD, INSTALL, COPY, DISTRIBUTE OR USE THE DATA FILES OR SOFTWARE.

Permission is hereby granted, free of charge, to any person obtaining a
copy of data files and any associated documentation (the "Data Files") or
software and any associated documentation (the "Software") to deal in the
Data Files or Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or sell
copies of the Data Files or Software, and to permit persons to whom the
Data Files or Software are furnished to do so, provided that either (a)
this copyright and permission notice appear with all copies of the Data
Files or Software, or (b) this copyright and permission notice appear in
associated Documentation.

THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF
THIRD PARTY RIGHTS.

IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS NOTICE
BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE DATA
FILES OR SOFTWARE.

Except as contained in this notice, the name of a copyright holder shall
not be used in advertising or otherwise to promote the sale, use or other
dealings in these Data Files or Software without prior written
authorization of the copyright holder.
