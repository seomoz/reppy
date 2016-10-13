import unittest

from reppy.agent import Agent


class AgentTest(unittest.TestCase):
    '''Tests about the Agent.'''

    def test_basic(self):
        '''Parses a basic example.'''
        agent = Agent().allow('/').disallow('/foo')
        self.assertEqual(len(agent.directives), 2)

    def test_checks_allowed(self):
        '''Answers the allowed question.'''
        agent = Agent().allow('/path')
        self.assertTrue(agent.allowed('/path'))
        self.assertTrue(agent.allowed('/elsewhere'))

    def test_honors_longest_first_priority(self):
        '''The longest matching rule takes priority.'''
        agent = Agent().disallow('/path').allow('/path/exception')
        self.assertTrue(agent.allowed('/path/exception'))
        self.assertFalse(agent.allowed('/path'))

    def test_robots_txt_allowed(self):
        '''Robots.txt is always allowed.'''
        agent = Agent().disallow('/robots.txt')
        self.assertTrue(agent.allowed('/robots.txt'))

    def test_disallow_none(self):
        '''Recognizes the "Disallow:" form of "Allow: /"'''
        agent = Agent().disallow('')
        self.assertTrue(agent.allowed('/anything'))

    def test_escaped_rule(self):
        '''Handles the case where the rule is escaped.'''
        agent = Agent().disallow('/a%3cd.html')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_unescaped_rule(self):
        '''Handles the case where the rule is unescaped.'''
        agent = Agent().disallow('/a<d.html')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_escaped_rule_wildcard(self):
        '''Handles the case where the wildcard rule is escaped.'''
        agent = Agent().disallow('/a%3c*')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_unescaped_rule_wildcard(self):
        '''Handles the case where the wildcard rule is unescaped.'''
        agent = Agent().disallow('/a<*')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_allow_url(self):
        '''The path can be appropriately extracted.'''
        agent = Agent().disallow('/path;params?query')
        self.assertFalse(agent.url_allowed('http://exmaple.com/path;params?query'))
