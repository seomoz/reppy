'''Holds the directives for a single user agent.'''

import url as URL

from . import logger
from .directive import BaseDirective


class Agent(object):
    '''The directives for a single user agent.'''

    def __init__(self, directives=None, delay=None):
        self._directives = directives or list()
        self.delay = None
        self._sorted = True

    @property
    def directives(self):
        '''Keep directives in descending order of precedence.'''
        if not self._sorted:
            self._directives.sort(reverse=True)
            self._sorted = True
        return self._directives

    def allow(self, query):
        '''Add an allow directive.'''
        self._directives.append(BaseDirective.allow(query))
        self._sorted = False
        return self

    def disallow(self, query):
        '''Add a disallow directive.'''
        if not query:
            # Special case: "Disallow:" means "Allow: /"
            self._directives.append(BaseDirective.allow(query))
        else:
            self._directives.append(BaseDirective.disallow(query))
        self._sorted = False
        return self

    def url_allowed(self, url):
        '''Return true if the path in url is allowed. Otherwise, false'''
        parsed = URL.parse(url).defrag().deuserinfo()
        parsed.scheme = ''
        parsed.host = ''
        return self.allowed(str(parsed))

    def allowed(self, query):
        '''Return true if the query is allowed. Otherwise, false.'''
        if query == '/robots.txt':
            return True
        sanitized = BaseDirective.sanitize(query)
        for directive in self.directives:
            if directive.match(sanitized):
                return directive.allowed
        return True
