'''Utility functions.'''

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
