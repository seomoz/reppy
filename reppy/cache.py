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

'''Caching fetch robots.txt files'''


import time
import requests
from requests.exceptions import (SSLError, ConnectionError, URLRequired, MissingSchema,
InvalidSchema, InvalidURL, TooManyRedirects)

from . import parser, logger, exceptions, Utility
from .parser import string_types


class RobotsCache(object):
    '''This object represents a cache of robots.txt rules for various sites.
    A policy for eviction can be set (or not set) by inheriting from this class
    '''
    default_ttl = 3600
    min_ttl = 60

    def __init__(self, *args, **kwargs):
        # The provided args and kwargs are used when fetching robots.txt with
        # a `requests.get`
        self.session = kwargs.pop('session', requests.Session())
        self.args = args
        self.disallow_forbidden = kwargs.pop('disallow_forbidden', True)
        self.kwargs = kwargs
        # A mapping of hostnames to their robots.txt rules
        self._cache = {}

    def find(self, url, fetch_if_missing=False, honor_ttl=True):
        '''Finds the rules associated with the particular url. Optionally, it
        can fetch the rules if they are missing.'''
        canonical = Utility.hostname(url)
        cached = self._cache.get(canonical)
        # If it's expired, we should get rid of it
        if honor_ttl and cached and cached.expired:
            del self._cache[canonical]
            cached = None
        # Should we fetch it if it's missing?
        if not cached and fetch_if_missing:
            return self.cache(url, *self.args, **self.kwargs)
        return cached

    def cache(self, url, *args, **kwargs):
        '''Like `fetch`, but caches the results, and does eviction'''
        fetched = self.fetch(url, *args, **kwargs)
        self._cache[Utility.hostname(url)] = fetched
        return fetched

    def fetch(self, url, *args, **kwargs):
        '''Fetch the robots.txt rules associated with the url. This does /not/
        cache the results. Any additional args are passed into `requests.get`
        '''
        try:
            # First things first, fetch the thing
            robots_url = Utility.roboturl(url)
            logger.debug('Fetching %s' % robots_url)
            req = self.session.get(robots_url, *args, **kwargs)
            ttl = max(self.min_ttl, Utility.get_ttl(req.headers, self.default_ttl))
            # And now parse the thing and return it
            return parser.Rules(robots_url, req.status_code, req.content,
                                time.time() + ttl,
                                disallow_forbidden=self.disallow_forbidden)
        except SSLError as exc:
            raise exceptions.SSLException(exc)
        except ConnectionError as exc:
            raise exceptions.ConnectionException(exc)
        except (URLRequired, MissingSchema, InvalidSchema, InvalidURL) as exc:
            raise exceptions.MalformedUrl(exc)
        except TooManyRedirects as exc:
            raise exceptions.ExcessiveRedirects(exc)
        except exceptions.BadStatusCode as exc:
            raise exceptions.BadStatusCode(exc)
        except Exception as exc:
            raise exceptions.ServerError(exc)

    def add(self, rules):
        '''Add a rules object to the cache. This is in case you ever want to
        '''
        self._cache[Utility.hostname(rules.url)] = rules

    def allowed(self, url, agent):
        '''Check whether the provided url is allowed for the provided user
        agent. The agent may be a short or long version'''
        if hasattr(url, '__iter__') and not isinstance(url, string_types):
            results = [self.allowed(u, agent) for u in url]
            return [u for u, allowed in zip(url, results) if allowed]
        return self.find(url, fetch_if_missing=True).allowed(
            url, Utility.short_user_agent(agent))

    def disallowed(self, url, agent):
        '''Check whether the provided url is disallowed. Equivalent to:
            not obj.allowed(url, agent)'''
        if hasattr(url, '__iter__') and not isinstance(url, string_types):
            results = [self.allowed(u, agent) for u in url]
            return [u for u, allowed in zip(url, results) if not allowed]
        return not self.allowed(url, agent)

    def delay(self, url, agent):
        '''Return the crawl delay rule'''
        return self.find(url, fetch_if_missing=True).delay(
            Utility.short_user_agent(agent))

    def sitemaps(self, url):
        '''Get the sitemaps of the provided url'''
        return self.find(url, fetch_if_missing=True).sitemaps

    def clear(self):
        '''Clear the cache'''
        self._cache = {}

    # Context Manager -- As a context manager, this always remembers to clear
    # the cache
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear()
