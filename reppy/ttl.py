'''Policies for setting the TTL on Robots objects.'''

import time

from . import logger
from .util import parse_date


class TTLPolicyBase(object):
    '''Policy for setting the TTL on Robots objects.'''

    def ttl(self, response):
        '''Get the caching TTL for a response.'''
        raise NotImplementedError('TTLPolicyBase does not implement ttl.')

    def expires(self, response):
        '''Determine when a response should expire.'''
        return time.time() + self.ttl(response)


class HeaderWithDefaultPolicy(TTLPolicyBase):
    '''TTL is based on headers, but falls back to a default, clamps to a minimum.'''

    def __init__(self, default, minimum):
        self.default = default
        self.minimum = minimum

    def ttl(self, response):
        '''Get the ttl from headers.'''
        # If max-age is specified in Cache-Control, use it and ignore any
        # Expires header, as per RFC2616 Sec. 13.2.4.
        cache_control = response.headers.get('cache-control')
        if cache_control is not None:
            for directive in cache_control.split(','):
                name, _, value = directive.lower().partition('=')
                name = name.strip()
                if name in ('no-store', 'must-revalidate', 'no-cache'):
                    return max(self.minimum, 0)
                elif name in ('s-maxage', 'max-age'):
                    try:
                        return max(self.minimum, int(value.strip()))
                    except ValueError:
                        logger.exception('Could not parse %s=%s', name, value)

        # Check the Expires header
        expires = response.headers.get('expires')
        if expires is not None:
            # Evaluate the expiration relative to the server-provided date
            date = response.headers.get('date')
            if date is not None:
                try:
                    date = parse_date(date)
                except ValueError:
                    logger.exception('Could not parse date string %s', date)
                    date = time.time()
            else:
                date = time.time()

            try:
                return max(self.minimum, parse_date(expires) - date)
            except ValueError:
                logger.exception('Could not parse date string %s', expires)

        return self.default
