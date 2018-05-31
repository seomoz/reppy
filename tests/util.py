'''Testing utilities.'''

import contextlib
import os

import six

import requests_mock


@contextlib.contextmanager
def requests_fixtures(*segments):
    '''Mock the paths provided in the fixture.'''
    # This reads in each of the asis files
    path = os.path.join('tests', 'asis', *segments)
    with requests_mock.mock() as mock:
        for name in os.listdir(path):
            with open(os.path.join(path, name), 'rb') as fin:
                content = iter(fin)

                # Read in the status line
                line = next(content)
                _, status, reason = line.split(b' ', 2)

                # Read in the headers
                headers = {}
                for line in content:
                    if not line.strip():
                        break

                    key, _, value = line.partition(b': ')
                    headers[key.strip()] = value.strip()

                # In python 3 mode, headers need to be text
                if six.PY3:
                    headers = {
                        k.decode('utf-8'): v.decode('utf-8') for k, v in headers.items()}

                mock.get(
                    '/%s' % name,
                    status_code=int(status),
                    reason=reason,
                    headers=headers,
                    content=b'\n'.join(content))
        yield
