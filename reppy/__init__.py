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

'''A robot exclusion protocol parser. Because I could not find a good one.'''

__maintainer__ = 'Dan Lecocq'
__copyright__ = '2011-2014 SEOmoz'
__license__ = 'SEOmoz'
__version__ = '0.3.0'
__author__ = 'Dan Lecocq'
__status__ = 'Development'
__email__ = 'dan@moz.com'

#####################################################
# All things logging
#####################################################
import logging

logger = logging.getLogger('reppy')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)

#####################################################
# A couple utilities
#####################################################
import sys
import re
import time
import email.utils
try:
    from urllib import parse as urlparse
except ImportError:
    # Python 2
    import urlparse

if sys.version_info[0] == 3:
    long = int

#####################################################
# Import our exceptions at the global level
#####################################################
from .exceptions import ServerError, ReppyException

class Utility(object):
    '''Utility methods'''
    @staticmethod
    def hostname(url):
        '''Return a normalized, canonicalized version of the url's hostname'''
        return urlparse.urlparse(url).netloc
    
    @staticmethod
    def roboturl(url):
        '''Return a normalized uri to the robots.txt'''
        parsed = urlparse.urlparse(url)
        return '%s://%s/robots.txt' % (parsed.scheme, parsed.netloc)

    @staticmethod
    def short_user_agent(strng):
        '''Return a default user agent string to match, based on strng. For
        example, for 'MyUserAgent/1.0', it will generate 'MyUserAgent' '''
        return re.sub('(\S+?)(\/.+)?', r'\1', strng)

    @staticmethod
    def parse_time(strng):
        '''Parse an HTTP-style (i.e. email-style) time into a timestamp'''
        v = email.utils.parsedate_tz(strng)
        if v is None:
            # Reject bad data
            raise ValueError("Invalid time.")
        if v[9] is None:
            # Default time zone is GMT/UTC
            v = list(v)  # @$%?? Dutch
            v[9] = 0
            v = tuple(v)
        return email.utils.mktime_tz(v)

    @staticmethod
    def get_ttl(headers, default):
        '''Extract the correct ttl from the provided headers, or default'''
        # Now, we'll determine the expiration
        ttl = None
        # If max-age is specified in Cache-Control, use it and ignore any
        # Expires header, as per RFC2616 Sec. 13.2.4.
        if headers.get('cache-control') is not None:
            for directive in headers['cache-control'].split(','):
                tokens = directive.lower().partition('=')
                t_name = tokens[0].strip()
                t_value = tokens[2].strip()
                # If we're not allowed to cache, then expires is now
                if t_name in ('no-store', 'must-revalidate'):
                    return 0
                elif t_name == 'no-cache' and t_value == '':
                    # Only honor no-cache if there is no =value after it
                    return 0
                elif t_name == 's-maxage':
                    try:
                        # Since s-maxage should override max-age, return
                        return long(t_value)
                    except ValueError:
                        # Couldn't parse s-maxage as an integer
                        continue
                elif t_name == 'max-age':
                    try:
                        ttl = long(t_value)
                    except ValueError:
                        # Couldn't parse max-age as an integer
                        continue

        # We should honor cache-control first, so if we found anything at
        # all, we should return that
        if ttl is not None:
            return ttl

        # Otherwise, we should use the expires tag
        expires = headers.get('expires')
        date = headers.get('date')
        if expires:
            if date is None:
                base = time.time()
            else:
                try:
                    base = Utility.parse_time(date)
                except ValueError:
                    base = time.time()
            try:
                return Utility.parse_time(expires) - base
            except ValueError:
                pass

        return ttl or default
