Internationalized Domain Names in Applications (IDNA)
=====================================================

A library to support the Internationalised Domain Names in Applications
(IDNA) protocol as specified in `RFC 5891 <http://tools.ietf.org/html/rfc5891>`_.
This version of the protocol is often referred to as “IDNA2008” and can 
produce different results from the earlier standard from 2003.

The library is also intended to act as a suitable drop-in replacement for
the “encodings.idna” module that comes with the Python standard library
but currently only supports the older 2003 specification.

Its basic functions are simply executed:

.. code-block:: pycon

    >>> import idna
    >>> idna.encode(u'ドメイン.テスト')
    'xn--eckwd4c7c.xn--zckzah'
    >>> print idna.decode('xn--eckwd4c7c.xn--zckzah')
    ドメイン.テスト

Packages
--------

The latest tagged release version is published in the PyPI repository:

.. image:: https://badge.fury.io/py/idna.svg
   :target: http://badge.fury.io/py/idna


Installation
------------

To install this library, you can use PIP:

.. code-block:: bash

    $ pip install idna

Alternatively, you can install the package using the bundled setup script:

.. code-block:: bash

    $ python setup.py install

This library should work with Python 2.7, and Python 3.3 or later.


Usage
-----

For typical usage, the ``encode`` and ``decode`` functions will take a domain
name argument and perform a conversion to an A-label or U-label respectively.

.. code-block:: pycon

    >>> import idna
    >>> idna.encode(u'ドメイン.テスト')
    'xn--eckwd4c7c.xn--zckzah'
    >>> print idna.decode('xn--eckwd4c7c.xn--zckzah')
    ドメイン.テスト

You may use the codec encoding and decoding methods using the
``idna.codec`` module.

.. code-block:: pycon

    >>> import idna.codec
    >>> print u'домена.испытание'.encode('idna')
    xn--80ahd1agd.xn--80akhbyknj4f
    >>> print 'xn--80ahd1agd.xn--80akhbyknj4f'.decode('idna')
    домена.испытание

Conversions can be applied at a per-label basis using the ``ulabel`` or ``alabel``
functions if necessary:

.. code-block:: pycon

    >>> idna.alabel(u'测试')
    'xn--0zwm56d'

Function calls from the Python built-in ``encodings.idna`` module are
mapping to their IDNA 2008 equivalents using the ``idna.compat`` module.
Simply substitute the ``import`` clause in your code to refer to the
new module name.

Exceptions
----------

All errors raised during the conversion following the specification should
raise an exception derived from the ``idna.IDNAError`` base class.

More specific exceptions that may be generated as ``idna.IDNABidiError``
when the error reflects an illegal combination of left-to-right and right-to-left
characters in a label; ``idna.InvalidCodepoint`` when a specific codepoint is
an illegal character in an IDN label (i.e. INVALID); and ``idna.InvalidCodepointContext``
when the codepoint is illegal based on its positional context (i.e. it is CONTEXTO
or CONTEXTJ but the contextual requirements are not satisfied.)

Testing
-------

The library has a test suite based on each rule of the IDNA specification, as
well as a subset of tests that are defined in Unicode Technical Standard 46,
`Unicode IDNA Compatibility Processing <http://unicode.org/reports/tr46/>`_.
Note that not all tests defined there are used, as TR46 defines tests for a 
normalisation approach beyond merely implementing IDNA2008.

The tests are run automatically on each commit to the master branch of the
idna git repository at Travis CI:

.. image:: https://travis-ci.org/kjd/idna.svg?branch=master
   :target: https://travis-ci.org/kjd/idna