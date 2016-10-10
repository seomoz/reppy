import unittest

from reppy import directive 


class BaseDirectiveTest(unittest.TestCase):
    '''Tests about the BaseDirectiveTest.'''

    def test_recognizes_allowed(self):
        '''Recognizes the allowed directive.'''
        self.assertTrue(directive.BaseDirective.parse('Allowed:').allowed)

    def test_recognizes_disallowed(self):
        '''Recognizes the disallowed directive.'''
        self.assertFalse(directive.BaseDirective.parse('Disallowed:').allowed)

    def test_exception_for_unrecognized(self):
        '''Raises an exception for unrecognized directives.'''
        with self.assertRaises(ValueError):
            directive.BaseDirective.parse('Foo: bar')

    def test_case_insensitive(self):
        '''Ignores the case of the directive.'''
        self.assertTrue(directive.BaseDirective.parse('aLLowed:').allowed)

    def test_ignores_passing(self):
        '''Ignores the padding around the directive.'''
        self.assertTrue(directive.BaseDirective.parse('  Allowed :').allowed)

    def test_returns_all_directive(self):
        '''Returns an AllDirective when possible.'''
        self.assertIsInstance(
            directive.BaseDirective.parse('Allowed:'),
            directive.AllDirective)

    def test_returns_string_directive(self):
        '''Returns a StringDirective when possible.'''
        self.assertIsInstance(
            directive.BaseDirective.parse('Allowed: /some/path'),
            directive.StringDirective)

    def test_returns_regex_directive(self):
        '''Returns a RegexDirective when necessary.'''
        self.assertIsInstance(
            directive.BaseDirective.parse('Allowed: /some/*/wildcard'),
            directive.RegexDirective)

    def test_raises_on_match(self):
        '''Does not implement match.'''
        with self.assertRaises(NotImplementedError):
            directive.BaseDirective(0, '', True).match('path')

    def test_supports_less_than(self):
        '''Can be compared.'''
        self.assertLess(
            directive.BaseDirective(0, '', True),
            directive.BaseDirective(1, 'a', True))


class StringDirectiveTest(unittest.TestCase):
    '''Tests about StringDirective.'''

    def test_matches_prefix(self):
        '''The query must start with the provided pattern to not match.'''
        self.assertTrue(
            directive.StringDirective(0, '/prefix', True).match('/prefix/url'))

    def test_does_not_match_prefix(self):
        '''The query must not start with the provided pattern to not match.'''
        self.assertFalse(
            directive.StringDirective(0, '/prefix', True).match('/different'))


class AllDirectiveTest(unittest.TestCase):
    '''Tests about the AllDirective.'''

    def test_matches_everything(self):
        '''Matches everything.'''
        self.assertTrue(
            directive.AllDirective(0, '', True).match('/anything'))


class RegexDirectiveTest(unittest.TestCase):
    '''Tests about the RegexDirective.'''

    def test_matches_beginning(self):
        '''Must match at the beginning to match.'''
        self.assertTrue(
            directive.RegexDirective(0, '/foo/*', True).match('/foo/bar'))

    def test_does_not_match_middle(self):
        '''Does not match on the middle of the query.'''
        self.assertFalse(
            directive.RegexDirective(0, '/foo/*', True).match('/whiz/foo/bar'))
