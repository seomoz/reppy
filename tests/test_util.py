import unittest

from reppy import util


class ParseDateTest(unittest.TestCase):
    '''Tests about parsing dates provided in headers.'''

    def test_invalid(self):
        '''Raises an error on an unparseable date.'''
        with self.assertRaises(ValueError):
            util.parse_date('Not a real date')

    def test_imf_fixdate(self):
        '''Successfully parses a IMF fixdate.'''
        self.assertEqual(
            util.parse_date('Sun, 06 Nov 1994 08:49:37 GMT'), 784111777)

    def test_rfc_850(self):
        '''An obsolete date format that is also supported.'''
        self.assertEqual(
            util.parse_date('Sunday, 06-Nov-94 08:49:37 GMT'), 784111777)

    def test_asctime(self):
        '''An obsolete date format that is also supported.'''
        self.assertEqual(
            util.parse_date('Sun Nov  6 08:49:37 1994'), 784111777)
