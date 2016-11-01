'''Robots.txt parsing.'''

import logging

logger = logging.getLogger('reppy')
handler = logging.StreamHandler()
formatter = logging.Formatter(
    ' | '.join([
        '[%(asctime)s]',
        'PID %(process)d',
        '%(levelname)s in %(module)s:%(funcName)s@%(lineno)s => %(message)s'
    ]))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)

from .robots import Robots, Agent
