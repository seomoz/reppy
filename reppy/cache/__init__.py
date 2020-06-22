'''A robots.txt cache.'''

from functools import partial
import threading
import time

from cachetools import LRUCache

from .policy import DefaultObjectPolicy, ReraiseExceptionPolicy
from ..exceptions import ReppyException
from ..robots import Robots, AllowNone, Agent
from .. import logger


class ExpiringObject(object):
    '''Wrap an object that expires over time.'''

    def __init__(self, factory):
        self.factory = factory
        self.lock = threading.Lock()
        self.obj = None
        self.expires = 0
        self.exception = None

    def get(self):
        '''Get the wrapped object.'''
        if (self.obj is None) or (time.time() >= self.expires):
            with self.lock:
                self.expires, self.obj = self.factory()
                if isinstance(self.obj, BaseException):
                    self.exception = self.obj
                else:
                    self.exception = None

        if self.exception:
            raise self.exception
        else:
            return self.obj


class BaseCache(object):
    '''A base cache class.'''

    DEFAULT_CACHE_POLICY = ReraiseExceptionPolicy(ttl=600)
    DEFAULT_TTL_POLICY = Robots.DEFAULT_TTL_POLICY

    def __init__(self, capacity, cache_policy=None, ttl_policy=None, *args, **kwargs):
        self.cache_policy = cache_policy or self.DEFAULT_CACHE_POLICY
        self.ttl_policy = ttl_policy or self.DEFAULT_TTL_POLICY
        self.cache = LRUCache(maxsize=capacity)
        self.args = args
        self.kwargs = kwargs

    def get(self, url):
        '''Get the entity that corresponds to URL.'''
        robots_url = Robots.robots_url(url)
        if robots_url not in self.cache:
            self.cache[robots_url] = ExpiringObject(partial(self.factory, robots_url))
        return self.cache[robots_url].get()

    def factory(self, url):
        '''
        Return (expiration, obj) corresponding to provided url, exercising the
        cache_policy as necessary.
        '''
        try:
            return self.fetch(url)
        except BaseException as exc:
            # Log the whole stack trace only if the exception is not a ReppyException
            # or if we do not have a default factory
            if isinstance(exc, ReppyException) and isinstance(self.cache_policy, DefaultObjectPolicy):
                logger.info('Reppy cache fetch error on %s; using factory.' % url)
            else:
                logger.exception('Reppy cache fetch error on %s' % url)

            return self.cache_policy.exception(url, exc)

    def fetch(self, url):
        '''Return (expiration, obj) corresponding to provided url.'''
        raise NotImplementedError('BaseCache does not implement fetch.')


class RobotsCache(BaseCache):
    '''A cache of Robots objects.'''

    DEFAULT_CACHE_POLICY = DefaultObjectPolicy(ttl=600, factory=AllowNone)

    def allowed(self, url, agent):
        '''Return true if the provided URL is allowed to agent.'''
        return self.get(url).allowed(url, agent)

    def fetch(self, url):
        '''Return (expiration, Robots) for the robots.txt at the provided URL.'''
        robots = Robots.fetch(
            url, ttl_policy=self.ttl_policy, *self.args, **self.kwargs)
        return (robots.expires, robots)


class AgentCache(BaseCache):
    '''A cache of Agent objects.'''

    DEFAULT_CACHE_POLICY = DefaultObjectPolicy(
        ttl=600, factory=lambda url: Agent().disallow('/'))

    def __init__(self, agent, *args, **kwargs):
        BaseCache.__init__(self, *args, **kwargs)
        self.agent = agent

    def allowed(self, url):
        '''Return true if the provided URL is allowed to self.agent.'''
        return self.get(url).allowed(url)

    def fetch(self, url):
        '''Return (expiration, Agent) for the robots.txt at the provided URL.'''
        robots = Robots.fetch(
            url, ttl_policy=self.ttl_policy, *self.args, **self.kwargs)
        return (robots.expires, robots.agent(self.agent))
