'''Utility functions.'''

import email
import string


def pairs(content):
    '''A generator of lowercase, stripped key-value pairs in contents' lines.'''
    for line in content.strip().split('\n'):
        # Remove any comments
        if '#' in line:
            line, _ = line.split('#', 1)

        key, _, value = [l.strip() for l in line.strip().partition(':')]

        if not key:
            continue

        yield (key.lower(), value)


def parse_date(string):
    '''Return a timestamp for the provided datestring, described by RFC 7231.'''
    parsed = email.utils.parsedate_tz(string)
    if parsed is None:
        raise ValueError("Invalid time.")
    if parsed[9] is None:
        # Default time zone is GMT/UTC
        parsed = list(parsed)
        parsed[9] = 0
    return email.utils.mktime_tz(parsed)
