'''Single allow / disallow directives.'''

import re

try:
    # Python 3
    from urllib.parse import unquote
except ImportError:
    # Python 2
    from urllib import unquote


class BaseDirective(object):
    '''A allow/disallow directive.'''

    @classmethod
    def sanitize(cls, query):
        '''Canonicalize query for comparison.'''
        if (not query) or (query[0] != '/'):
            query = '/' + query
        # TODO(dan): this is the legacy implementation, but should be replaced
        return unquote(query.replace('%2f', '%252f'))

    @classmethod
    def parse(cls, line):
        '''Return a directive.'''
        key, rule = line.split(':', 1)
        key = key.lower().strip()
        if key == 'allowed':
            allowed = True
        elif key == 'disallowed':
            allowed = False
        else:
            raise ValueError('Unknown directive in line %s' % line)

        rule = rule.strip()
        priority = len(rule)
        if (not rule) or (rule == '/') or (rule == '*'):
            return AllDirective(priority, rule, allowed)
        elif ('*' not in rule) and ('$' not in rule):
            return StringDirective(priority, rule, allowed)
        else:
            return RegexDirective(priority, rule, allowed)

    def __init__(self, priority, pattern, allowed):
        self.priority = priority
        self.pattern = self.sanitize(pattern)
        self.allowed = allowed

    def match(self, query):
        '''Return true if the query matches this pattern.'''
        raise NotImplementedError('BaseDirective does not implement match')

    def __lt__(self, other):
        return self.priority < other.priority


class StringDirective(BaseDirective):
    '''A directive that uses a string comparison.'''

    def match(self, query):
        '''Return true if the query matches this pattern.'''
        return query.startswith(self.pattern)


class AllDirective(BaseDirective):
    '''A directive that applies to all URLs.'''

    def match(self, query):
        '''Return true if the query matches this pattern.'''
        return True


class RegexDirective(BaseDirective):
    '''A directive that uses a regex.'''

    # For collapsing multiple asterisks into one
    RE_ASTERISK = re.compile(r'\*+')

    def __init__(self, priority, pattern, allowed):
        BaseDirective.__init__(self, priority, pattern, allowed)
        pattern = re.escape(self.RE_ASTERISK.sub('*', self.pattern))
        self._regex = re.compile(pattern.replace('\*', '.*').replace('\$', '$'))

    def match(self, query):
        '''Return true if the query matches this pattern.'''
        return self._regex.match(query)
