from __future__ import unicode_literals, absolute_import, print_function

from sensetdp.api import API

import vcr
import os
import six

from sensetdp.auth import HTTPBasicAuth

if six.PY3:
    import unittest
else:
    import unittest2 as unittest

username = os.environ.get('SENSET_DP_USERNAME', 'username')
password = os.environ.get('SENSET_DP_PASSWORD', 'password')
use_replay = os.environ.get('USE_REPLAY', False)


tape = vcr.VCR(
    cassette_library_dir='cassettes',
    filter_headers=['Authorization'],
    serializer='json',
    # Either use existing cassettes, or never use recordings:
    record_mode='none' if use_replay else 'all',
)


class SenseTTestCase(unittest.TestCase):
    def setUp(self):
        self.auth = HTTPBasicAuth(username, password)
        self.api = API(self.auth)
        self.api.retry_count = 0
        self.api.retry_delay = 5
