import unittest

from reppy import util


class PairsTest(unittest.TestCase):
    '''Tests about how we make pairs.'''

    def test_skips_blanks(self):
        '''Skips blank lines.'''
        content = '''
            hello

            world
        '''
        lines = [
            ('hello', ''),
            ('world', '')
        ]
        self.assertEqual(lines, list(util.pairs(content)))

    def test_strips_keys_and_values(self):
        '''Strips leading and trailing whitespace on keys and values.'''
        content = '''
            hello:  world\t
        '''
        lines = [
            ('hello', 'world')
        ]
        self.assertEqual(lines, list(util.pairs(content)))

    def test_lowercases_keys(self):
        '''Makes the key lowercase.'''
        content = '''
            HeLLo: World
        '''
        lines = [
            ('hello', 'World')
        ]
        self.assertEqual(lines, list(util.pairs(content)))

    def test_does_not_trip_on_multiple_colons(self):
        '''Does not fail when multiple colons are present.'''
        content = '''
            hello: world: 2
        '''
        lines = [
            ('hello', 'world: 2')
        ]
        self.assertEqual(lines, list(util.pairs(content)))

    def test_skips_comments(self):
        '''Skips comment lines.'''
        content = '''
            # This is a comment.
        '''
        lines = []
        self.assertEqual(lines, list(util.pairs(content)))

    def test_omits_comments(self):
        '''Removes the comment portion of a line.'''
        content = '''
            hello: world # this is a comment
        '''
        lines = [
            ('hello', 'world')
        ]
        self.assertEqual(lines, list(util.pairs(content)))


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
