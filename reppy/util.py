'''Utility functions.'''

import email


def parse_date(string):
    '''Return a timestamp for the provided datestring, described by RFC 7231.'''
    parsed = email.utils.parsedate_tz(string)
    if parsed is None:
        raise ValueError("Invalid time.")
    parsed = list(parsed)
    # Default time zone is GMT/UTC
    parsed[9] = 0 if parsed[9] is None else parsed[9]
    return email.utils.mktime_tz(parsed)
