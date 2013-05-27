#!/usr/bin/env python
#
#   Tests against the compliance suite from Unicode Technical Report 46.
#   Some of these tests are not applicable for IDNA 2008 conformance,
#   and TR 46 specifies additional out-of-scope processing. These test
#   suite is retrieved from http://unicode.org/Public/idna/6.2.0/IdnaTest.txt
#   and has been gzipped as some of the esoteric codepoints in the file
#   can break text editors.
#

from collections import defaultdict
import gzip
import unittest
import re
import sys
sys.path.append('..')
import idna

def expand_unicode_notation(s):

	while s.find("\\u") > 0:
		i = s.find("\\u")
		v = unichr(int(s[i + 2:i + 6], 16))
		s = s[0:i] + v.encode('utf-8') + s[i + 6:]
	return s

def split_labels(s):

	yield re.compile(u"[\u002E\u3002\uFF0E\uFF61]").split(input)

class TR46Tests(unittest.TestCase):

	def setUp(self):

		self.tounicode_fails = defaultdict(list)
		self.toascii_fails = defaultdict(list)
		self.tounicode_success = {}
		self.toascii_success = {}

		for line in gzip.open("IdnaTest.txt.gz").readlines():
			line = line.strip()
			if not line or line[0] == '#':
				continue
			if line.find('NV8') > 0:
				continue
			if line.find('#'):
				line = line.split('#')[0]
			line = expand_unicode_notation(line)
			columns = line.split(';')
			columns = [x.strip() for x in columns]

			if columns[0] != 'B' and columns[0] != 'N':
				continue

			if columns[2] and columns[2][0] == '[':
				for failure_type in columns[2][1:-1].split(' '):
					self.tounicode_fails[failure_type].append(columns[1])
			else:
				self.tounicode_success[columns[1]] = columns[2]

			if columns[3] and columns[3][0] == '[':
				for failure_type in columns[3][1:-1].split(' '):
					self.toascii_fails[failure_type].append(columns[1])
			else:
				self.toascii_success[columns[1]] = columns[3]

	def testA3(self):
		""" TR46-A3 Punycode conversion failure """
		for s in self.tounicode_fails['A3']:
			self.assertRaises(UnicodeError, idna.decode, s)
		#for s in self.toascii_fails['A3']:
		#	print s
		#	self.assertRaises(UnicodeError, idna.encode, s)


	def testA4_1(self):
		""" TR46-A4_1 Length error (must be 1-253 octets) """
		for s in self.tounicode_fails['A4_1']:
			self.assertEqual(False, idna.valid_string_length, s)

	#def testA4_2(self):
	# 	""" TR46-A4_2 Label length error (must be 1-63 octets) """
	# 	for s in self.tounicode_fails['A4_2']:
	# 		self.assertEqual(False, idna.valid_label_length, s)

	def testB1(self):
		""" TR46-B1 First character must be L, R or AL """
		for s in self.tounicode_fails['B1']:
			self.assertRaises(idna.IDNAError, idna.decode, s)
	#
	def testB2(self):
		""" TR46-B2 Invalid directionality for RTL label """
		for s in self.tounicode_fails['B2']:
			self.assertRaises(idna.IDNAError, idna.decode, s)
	#
	def testB3(self):
		""" TR46-B3 Invalid final characters for RTL label """
		for s in self.tounicode_fails['B3']:
			self.assertRaises(idna.IDNAError, idna.decode, s)
	#
	def testB4(self):
		""" TR46-B4 Invalid EN/AN commingling in RTL label """
		for s in self.tounicode_fails['B4']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testB5(self):
		""" TR46-B5 Invalid directionality for LTR label """
		for s in self.tounicode_fails['B5']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testB6(self):
		""" TR46-B6 Invalid final characters for LTR label """
		for s in self.tounicode_fails['B6']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testC1(self):
		""" TR46-C1 Zero-Width Non-Joiner Invalid Context """
		for s in self.tounicode_fails['C1']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testC2(self):
		""" TR46-C2 Zero-Width Joiner Invalid Context """
		for s in self.tounicode_fails['C2']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testP1(self):
		""" TR46-P1 Mapping Invalid Code Point """
		for s in self.tounicode_fails['P1']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	#def testV1(self):
	#	""" TR46-V1 Must be Unicode Normalization Form NFC """
	#	for s in self.tounicode_fails['V1']:
	#		print s
	#		self.assertRaises(UnicodeError, idna.decode, s)

	def testV2(self):
		""" TR46-V2 Must not contain U+002D at 3rd and 4th position """
		for s in self.tounicode_fails['V2']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testV3(self):
		""" TR46-V3 Must not begin nor end with U+002D """
		for s in self.tounicode_fails['V3']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	def testV5(self):
		""" TR46-V5 Must not begin with a combining mark """
		for s in self.tounicode_fails['V5']:
			self.assertRaises(idna.IDNAError, idna.decode, s)

	# def testV6(self):
	# 	""" TR46-V6 Unsatisfactory mapping value """
	# 	pass

	def testValidUlabel(self):
		for s in self.tounicode_success:
			self.assertEqual(idna.decode(s), self.tounicode_success[s])

	def testValidAlabel(self):
		for s in self.toascii_success:
			self.assertEqual(idna.encode(s.decode('utf-8')), self.toascii_success[s])

if __name__ == '__main__':
	unittest.main()