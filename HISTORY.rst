.. :changelog:

History
-------

1.1 (2015-01-27)
++++++++++++++++

- Use IDNA properties from Unicode 6.3.0. Internet Architecture Board (IAB)
  issued statement recommending against the use of Unicode 7.0.0 until
  issues relating to U+08A1 codepoint are resolved. See http://goo.gl/Ed1n0K
- Identify some cases when label would be too longer to be a legal DNS name
  and raise an exception. (Thanks, Ed Lewis)

1.0 (2014-10-12)
++++++++++++++++

- Update IDNA properties for Unicode 7.0.0.

0.9 (2014-07-18)
++++++++++++++++

- Fix issue with non-UTF-8 environments reading the README file
  now that it contains non-ASCII. (Thanks, Tom Prince)
- Codec functions are useful, so they are separated into their own
  module, rather than just existing for compatibility reasons.
- Add LICENSE file.

0.8 (2014-07-09)
++++++++++++++++

- Added MANIFEST.in for correct source distribution compilation.

0.7 (2014-07-09)
++++++++++++++++

- Filled out missing tests for various functions.
- Fix bug in CONTEXTO validation for Greek lower numeral sign (U+0375)
- Fix bug in CONTEXTO validation for Japanese middle dot (U+30FB)
- Improved documentation
- Move designation to Stable

0.6 (2014-04-29)
++++++++++++++++

- Minor improvements to Python 3 support, tests (Thanks, Derek Wilson)

0.5 (2014-02-05)
++++++++++++++++

- Update IDNA properties for Unicode 6.3.0.

0.4 (2014-01-07)
++++++++++++++++

- Fix trove classifier for Python 3. (Thanks, Hynek Schlawack)

0.3 (2013-07-18)
++++++++++++++++

- Ported to Python 3.

0.2 (2013-07-16)
++++++++++++++++

- Improve packaging.
- More conformant, passes all relevant tests in the Unicode TR46 test suite.

0.1 (2013-05-27)
++++++++++++++++

- First proof-of-concept version.
