from __future__ import unicode_literals, absolute_import, print_function

import json
import pickle
import uuid

from unittest2.case import skip

from sensetdp.models import Organisation, Group, Platform
from .config import *

import six
if six.PY3:
    import unittest
else:
    import unittest2 as unittest


class ApiTestCase(SenseTTestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()

    def generate_platform(self):
        o = Organisation()
        o.id = "utas"

        g = Group()
        g.id = "ionata_sandbox"

        p = Platform()
        p.id = "test_platform_{0}".format(uuid.uuid4())
        p.name = "A Platform create for unittests"
        p.organisations = [o]
        p.groups = [g]
        return p

    @skip("Permissions issues")
    def test_create_platform(self):
        """
        Platform creation test, no clean up
        :return: None
        """
        # create
        p = self.generate_platform()

        required_json = json.dumps({
            "id": p.id,
            "name": p.name,
            "organisationid": p.organisations[0].id,
            "groupids": [
                p.groups[0].id
            ],
            "streamids": [
            ],
            "deployments": [
            ]
        }, sort_keys=True)  # be explict with key order since dumps gives us a string

        actual_json = p.to_json("create")

        # verify json
        assert actual_json == required_json

        created_platform = self.api.create_platform(p)

        # verify
        assert created_platform.id == p.id
        assert created_platform.name == p.name

    @skip("Permissions issues")
    def test_update_platform(self):
        """
        Platform update test, no clean ups
        :return: None
        """
        # create
        p = self.generate_platform()
        created_platform = self.api.create_platform(p)

        # update, by appending id to name attr
        created_platform.name += created_platform.id
        updated_platform = self.api.update_platform(created_platform)

        # verify
        assert updated_platform.name == created_platform.name

    @skip("Permissions issues")
    def test_delete_platform(self):
        """
        Platform deletion test, create and cleanup
        :return: None
        """
        # create
        p = self.generate_platform()
        created_platform = self.api.create_platform(p)
        created_platform.name += created_platform.id

        # delete
        deleted_platform = self.api.destroy_platform(created_platform)

        # verify
        assert deleted_platform is None

    #@tape.use_cassette('test_verify_init_stream.json')
    def test_verify_init_stream(self):
        # required
        platformid = '05b31a8b-0549-4484-a1b9-a05b89fc677f'
        stream = {}
        stream['id'] = platformid + '_location'
        stream['resulttype'] = 'geolocationvalue'
        stream['groupids'] = ['tourtracker']
        stream['samplePeriod'] = 'PT10S'
        stream['reportingPeriod'] = 'P1D'
        stream['organisationid'] = 'utas'
        stream['streamMetadata'] = {
            #  'type': '.GeoLocationStreamMetaData', # type is not used or returned after creation
            'interpolationType': 'http://www.opengis.net/def/waterml/2.0/interpolationType/Continuous',

            'accumulationAnchor': None,
            'accumulationInterval': None,
            'cummulative': None,
            'observedProperty': None,
            'timezone': None,
            'unitOfMeasure': None,
        }
        required_json = json.dumps(stream, sort_keys=True)  # be explict with key order since dumps gives us a string

        # get from api
        s = self.api.get_stream(id=stream['id'])
        actual_json = s.to_json("get")

        # verify json
        assert actual_json == required_json
