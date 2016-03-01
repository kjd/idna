"""
A library to support the Internationalised Domain Names in Applications
(IDNA) protocol as specified in RFC 5890 et.al. This new methodology,
known as IDNA2008, can generate materially different results to the
previous standard. The library can act as a drop-in replacement for
the "encodings.idna" module.
"""

import sys
from setuptools import setup
import io

version = "2.0"

def main():

    python_version = sys.version_info[:2]
    if python_version < (2,6):
        raise SystemExit("Sorry, Python 2.6 or newer required")

    arguments = {
        'name': 'idna',
        'packages': ['idna'],
        'version': version,
        'description': 'Internationalized Domain Names in Applications (IDNA)',
        'long_description': io.open("README.rst", encoding="UTF-8").read(),
        'author': 'Kim Davies',
        'author_email': 'kim@cynosure.com.au',
        'license': 'BSD-like',
        'url': 'https://github.com/kjd/idna',
        'package_data': {'idna': ['idnadata.dat']},
        'classifiers': [
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Internet :: Name Service (DNS)',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Utilities',
        ],
        'test_suite': 'tests',
    }

    setup(**arguments)

if __name__ == '__main__':
    main()
