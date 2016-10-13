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
