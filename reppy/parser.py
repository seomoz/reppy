#! /usr/bin/env python
#
# Copyright (c) 2011 SEOmoz
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''Classes for parsing robots.txt files'''

import sys
import re
import time
import codecs
try:
    from urllib import parse as urlparse
    from urllib.parse import unquote
except ImportError:
    # Python 2
    import urlparse
    from urllib import unquote

from . import logger, exceptions, Utility

if sys.version_info[0] == 3:
    string_types = str
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
    text_type = unicode
    binary_type = str


class Agent(object):
    '''Represents attributes for a given robot'''
    pathRE = re.compile(r'^([^\/]+\/\/)?([^\/]+)?(/?.+?)$', re.M)

    def __init__(self):
        self.allowances = []
        self.delay = None

    @staticmethod
    def extract_path(url):
        '''Extracts path (with parameters) from given url, if url is already a
        path (starts with /) it's rerurned without modifications. In case url
        is empty or only contains domain without trailing slash, returns a
        single slash.'''
        # This method was actually contributed by Wiktor Bachnik (wbachnik)
        # but because I forgot to rebase before my branch, this is going to
        # appear in a different commit :-/
        if len(url) == 0:
            # empty, assume /
            path = '/'
        elif url[0] == '/':
            # url is already a path
            path = url
        else:
            # url is a proper url scheme://host/...
            parts = urlparse.urlsplit(url)
            needed_parts = urlparse.SplitResult(scheme='', netloc='',
                path=parts.path, query=parts.query, fragment='')
            path = needed_parts.geturl()
            if len(path) == 0:
                # case for http://example.com
                path = '/'
            # If there was a question mark in the url, but no query string
            # then we must still preserve the question mark.
            if (not parts.query) and ('?' in url):
                path = path + '?'
        return path

    def allowed(self, url):
        '''Can I fetch a given URL?'''
        path = unquote(self.extract_path(url).replace('%2f', '%252f'))
        if path == '/robots.txt':
            return True
        allowed = [a for a in self.allowances if a[1].match(path)]
        if allowed:
            return max(allowed)[2]
        else:
            return True


class Rules(object):
    '''A class that represents a set of agents, and can select them
    appropriately. Associated with one robots.txt file.'''
    def __init__(self, url, status, content, expires, disallow_forbidden=True):
        self.agents = {}
        self.sitemaps = []
        # Information about this
        self.url = url
        self.status = status
        self.expires = expires
        if status == 200:
            self.parse(content)
        elif status in (401, 403):
            logger.warn('Access forbidden to site %s (%i)' % (
                url, status))
            if disallow_forbidden:
                self.parse('''User-agent: *\nDisallow: /''')
            else:
                self.parse('')
        elif status >= 400 and status < 500:
            logger.info('Assuming unrestricted access %s (%i)' % (
                url, status))
            self.parse('')
        elif status >= 500:
            raise exceptions.BadStatusCode(
                'Remote server returned ServerError %i' % status, status)
        else:
            raise exceptions.ReppyException(
                exceptions.ServerError(
                    'Remote server returned status %i' % status, status))

    @property
    def ttl(self):
        '''Get the time left before expiration'''
        return self.expires - time.time()

    @property
    def expired(self):
        '''Has this rules object expired?'''
        return self.ttl <= 0

    @staticmethod
    def _regex_rule(rule):
        '''Make a regex that matches the patterns expressable in robots.txt'''
        # If the string doesn't start with a forward slash, we'll insert it
        # anyways:
        #   http://code.google.com/web/controlcrawlindex/docs/robots_txt.html
        # As such, the only permissible start characters for a rule like this
        # are
        # '*' and '/'
        if rule and rule[0] != '/' and rule[0] != '*':
            rule = '/' + rule
        tmp = re.escape(unquote(rule.replace('%2f', '%252f')))
        return re.compile(tmp.replace('\*', '.*').replace('\$', '$'))

    def __getitem__(self, agent):
        '''Find the agent given a string for it'''
        agent = Utility.short_user_agent(agent)
        return self.agents.get(agent.lower(), self.agents.get('*'))

    def parse(self, content):
        '''Parse the given string and store the resultant rules'''
        # The agent we're currently working with
        cur = Agent()

        # If we didn't get a header indicating unicode, we have an 8-bit
        # string here. Suspect undeclared UTF-8 or UTF-16 and look for a
        # leading BOM. If there is one, attempt to decode. If the decoding
        # fails, proclaim the robots.txt file to be garbage and ignore it.
        if isinstance(content, binary_type):
            try:
                if content.startswith(codecs.BOM_UTF8):
                    content = content.decode('utf-8').lstrip(
                        text_type(codecs.BOM_UTF8, 'utf-8'))
                elif content.startswith(codecs.BOM_UTF16):
                    content = content.decode('utf-16')
                else:
                    content = content.decode('utf-8', 'ignore')
            except UnicodeDecodeError:  # pragma: no cover
                # This is a very rare and difficult-to-reproduce exception
                logger.error('Too much garbage! Ignoring %s' % self.url)
                self.agents['*'] = Agent()
                return

        # The name of the current agent. There are a couple schools of thought
        # here. For example, by including a default agent, the robots.txt's
        # author's intent is clearly accommodated if a Disallow line appears
        # before the a User-Agent line. However, how hard is it to follow the
        # standard? If you're writing a robots.txt, you should be able to
        # write it correctly.
        curname = '*'
        last = ''
        for rawline in content.splitlines():
            # Throw away any leading or trailing whitespace
            line = rawline.strip()

            # Throw away comments, and ignore blank lines
            octothorpe = line.find('#')
            if octothorpe >= 0:
                line = line[:octothorpe]
            if line == '':
                continue

            # Non-silently ignore lines with no ':' delimiter
            if ':' not in line:
                logger.warn('Skipping garbled robots.txt line %s' %
                    repr(rawline))
                continue

            # Looks valid. Split and interpret it
            key, val = [x.strip() for x in line.split(':', 1)]
            key = key.lower()
            if key == 'user-agent' or key == 'useragent':
                # Store the current working agent
                if cur:
                    self.agents[curname] = cur
                curname = val.lower()
                if last != 'user-agent' and last != 'useragent':
                    # If the last line was a user agent, then all lines
                    # below also apply to the last user agent. So, we'll
                    # have this user agent point to the one we declared
                    # for the previously-listed agent
                    cur = self.agents.get(curname, None) or Agent()
            elif cur and key == 'disallow':
                if len(val):
                    cur.allowances.append(
                        (len(val), self._regex_rule(val), False))
            elif cur and key == 'allow':
                cur.allowances.append(
                    (len(val), self._regex_rule(val), True))
            elif cur and key == 'crawl-delay':
                cur.delay = float(val)
            elif cur and key == 'sitemap':
                self.sitemaps.append(val)
            else:
                logger.warn('Unknown key in robots.txt line %s' %
                    repr(rawline))
            last = key

        # Now store the user agent that we've been working on
        self.agents[curname] = cur or Agent()

    def allowed(self, url, agent):
        '''We try to perform a good match, then a * match'''
        if hasattr(url, '__iter__') and not isinstance(url, string_types):
            results = [self[agent].allowed(u) for u in url]
            return [u for u, allowed in zip(url, results) if allowed]
        return self[agent].allowed(url)

    def disallowed(self, url, agent):
        '''For completeness'''
        return not self.allowed(url, agent)

    def delay(self, agent):
        '''How fast can the specified agent legally crawl this site?'''
        return self[agent].delay
