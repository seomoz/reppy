'''Policies for caching.'''

import time


class CachePolicyBase(object):
    '''Policy for caching.'''

    def exception(self, url, exception):
        '''What to return when there's an exception.'''
        raise NotImplementedError('CachePolicyBase does not implement exception.')


class DefaultObjectPolicy(object):
    '''Return a default object on exception.'''

    def __init__(self, ttl, factory):
        self.ttl = ttl
        self.factory = factory

    def exception(self, url, exception):
        '''What to return when there's an exception.'''
        return (time.time() + self.ttl, self.factory(url))


class ReraiseExceptionPolicy(object):
    '''Reraise the exception.'''

    def __init__(self, ttl):
        self.ttl = ttl

    def exception(self, url, exception):
        '''What to return when there's an exception.'''
        return (time.time() + self.ttl, exception)
