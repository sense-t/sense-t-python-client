from __future__ import unicode_literals, absolute_import, print_function
from .config import *

import six
if six.PY3:
    import unittest
else:
    import unittest2 as unittest


class AuthTestCase(SenseTTestCase):
    def test_credentials_configured(self):
        assert self.api.me().id == username

    def test_roles(self):
        api_roles = self.api.me().roles
        assert len(api_roles) == 2
        assert api_roles[0].id == "TourTrackerAdmin"
