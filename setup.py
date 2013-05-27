"""
A library to support the Internationalised Domain Names in Applications
(IDNA) protocol as specified in RFC 5890 et.al. This new methodology,
known as IDNA2008, can generate materially different results to the
previous standard. The library can act as a drop-in replacement for
the "encodings.idna" module.
"""

import sys
from setuptools import setup, find_packages

version = "0.1"

def main():

	python_version = sys.version_info[:2]
	if python_version < (2,6):
		raise SystemExit("Sorry, Python 2.6 or newer required")
	if python_version[0] == 3 and python_version < (3,3):
		raise SystemExit("Sorry, Python 3.3 or newer required")

	arguments = {
		'name': 'idna',
		'packages': find_packages(),
		'provides': ['idna'],
		'version': version,
		'description': 'IDNA',
		'long_description': __doc__,
		'author': 'Kim Davies',
		'author_email': 'kim@cynosure.com.au',
		'license': 'BSD-like',
		'url': 'https://github.com/kjd/idna',
		'classifiers': [
			'Development Status :: 3 - Alpha',
			'Intended Audience :: Developers',
			'Intended Audience :: System Administrators',
			'License :: OSI Approved :: BSD License',
			'Operating System :: OS Independent',
			'Topic :: Internet :: Name Service (DNS)',
			'Topic :: Software Development :: Libraries :: Python Modules',
			'Topic :: Utilities',
		],
	}
	
	setup(**arguments)

if __name__ == '__main__':
	main()
