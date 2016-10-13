import unittest

from reppy import directive 


class BaseDirectiveTest(unittest.TestCase):
    '''Tests about the BaseDirective.'''

    def test_recognizes_allowed(self):
        '''Recognizes the allowed directive.'''
        self.assertTrue(directive.BaseDirective.allow('').allowed)

    def test_recognizes_disallowed(self):
        '''Recognizes the disallowed directive.'''
        self.assertFalse(directive.BaseDirective.disallow('').allowed)

    def test_returns_all_directive(self):
        '''Returns an AllDirective when possible.'''
        self.assertIsInstance(
            directive.BaseDirective.allow(''),
            directive.AllDirective)

    def test_returns_string_directive(self):
        '''Returns a StringDirective when possible.'''
        self.assertIsInstance(
            directive.BaseDirective.allow('/some/path'),
            directive.StringDirective)

    def test_returns_regex_directive(self):
        '''Returns a RegexDirective when necessary.'''
        self.assertIsInstance(
            directive.BaseDirective.allow('/some/*/wildcard'),
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

    def test_exact_match(self):
        '''The query may be an exact match.'''
        self.assertTrue(
            directive.StringDirective(0, '/prefix', True).match('/prefix'))

    def test_matches_prefix(self):
        '''The query must start with the provided pattern to not match.'''
        self.assertTrue(
            directive.StringDirective(0, '/prefix', True).match('/prefix/url'))

    def test_does_not_match_prefix(self):
        '''The query must not start with the provided pattern to not match.'''
        self.assertFalse(
            directive.StringDirective(0, '/prefix', True).match('/different'))

    def test_escaped_rule(self):
        '''Handles the case where the rule is escaped.'''
        rule = directive.StringDirective(0, '/a%3cd.html', True)
        self.assertTrue(rule.match('/a<d.html'))

    def test_unescaped_rule(self):
        '''Handles the case where the rule is unescaped.'''
        rule = directive.StringDirective(0, '/a<d.html', True)
        self.assertTrue(rule.match('/a<d.html'))

    def test_foward_slash_escaped(self):
        '''Ensures escaped forward slashes are not matched with unescaped'''
        rule = directive.StringDirective(0, '/a%2fb.html', True)
        self.assertTrue(rule.match('/a%2fb.html'))
        self.assertFalse(rule.match('/a/b.html'))

    def test_foward_slash_unescaped(self):
        '''Ensures unescaped forward slashes are not matched with escaped'''
        rule = directive.StringDirective(0, '/a/b.html', True)
        self.assertTrue(rule.match('/a/b.html'))
        self.assertFalse(rule.match('/a%2fb.html'))

    def test_query(self):
        '''Queries must appear in the provided order'''
        rule = directive.StringDirective(0, '/a?howdy', True)
        self.assertTrue(rule.match('/a?howdy'))
        self.assertTrue(rule.match('/a?howdy=there'))
        self.assertFalse(rule.match('/a?hey=everyone'))

    def test_missing_leading_slash(self):
        '''Directives missing a leading slash have one applied.'''
        rule = directive.StringDirective(0, 'hello', True)
        self.assertTrue(rule.match('/hello'))

    def test_str(self):
        '''Has a resonable string representation.'''
        rule = directive.StringDirective(0, 'hello', True)
        self.assertEqual(
            str(rule), '<StringDirective priority=0, pattern=/hello, allowed=True>')


class AllDirectiveTest(unittest.TestCase):
    '''Tests about the AllDirective.'''

    def test_matches_everything(self):
        '''Matches everything.'''
        self.assertTrue(
            directive.AllDirective(0, '', True).match('/anything'))

    def test_str(self):
        '''Has a resonable string representation.'''
        rule = directive.AllDirective(0, '', True)
        self.assertEqual(
            str(rule), '<AllDirective priority=0, pattern=/, allowed=True>')


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

    def test_any_with_query(self):
        '''Matches any path with a query.'''
        self.assertTrue(
            directive.RegexDirective(0, '/*?', True).match('/path?query'))

    def test_middle_wildcard(self):
        '''Matches wildcards in the middle.'''
        rule = directive.RegexDirective(0, '/folder*name/', True)
        self.assertTrue(rule.match('/folder-middle-name/'))

    def test_matches_end(self):
        '''Can match the end of a path.'''
        rule = directive.RegexDirective(0, '/*.gif$', True)
        self.assertTrue(rule.match('/funny.gif'))
        self.assertFalse(rule.match('/funny.gifs/path'))

    def test_many_wildcards(self):
        '''Multiple consecutive wildcards are compressed into one.'''
        rule = directive.RegexDirective(0, '/********************************.css', True)
        self.assertTrue(rule.match('/style.css'))

    def test_multiple_wildcards(self):
        '''Multiple wildcards are supported.'''
        rule = directive.RegexDirective(0, '/one/*/three/*/five', True)
        self.assertTrue(rule.match('/one/two/three/four/five'))

    def test_escaped_rule(self):
        '''Handles the case where the rule is escaped.'''
        rule = directive.RegexDirective(0, '/a%3cd*', True)
        self.assertTrue(rule.match('/a<d.html'))

    def test_unescaped_rule(self):
        '''Handles the case where the rule is unescaped.'''
        rule = directive.RegexDirective(0, '/a<d*', True)
        self.assertTrue(rule.match('/a<d.html'))

    def test_foward_slash_escaped(self):
        '''Ensures escaped forward slashes are not matched with unescaped'''
        rule = directive.RegexDirective(0, '/a%2fb*', True)
        self.assertTrue(rule.match('/a%2fb.html'))
        self.assertFalse(rule.match('/a/b.html'))

    def test_foward_slash_unescaped(self):
        '''Ensures unescaped forward slashes are not matched with escaped'''
        rule = directive.RegexDirective(0, '/a/b*', True)
        self.assertTrue(rule.match('/a/b.html'))
        self.assertFalse(rule.match('/a%2fb.html'))

    def test_query(self):
        '''Queries must appear in the provided order'''
        rule = directive.RegexDirective(0, '/a?howdy', True)
        self.assertTrue(rule.match('/a?howdy'))
        self.assertTrue(rule.match('/a?howdy=there'))
        self.assertFalse(rule.match('/a?hey=everyone'))

    def test_missing_leading_slash(self):
        '''Directives missing a leading slash have one applied.'''
        rule = directive.RegexDirective(0, 'hello', True)
        self.assertTrue(rule.match('/hello'))

    def test_str(self):
        '''Has a resonable string representation.'''
        rule = directive.RegexDirective(0, '', True)
        self.assertEqual(
            str(rule), '<RegexDirective priority=0, pattern=/, allowed=True>')
