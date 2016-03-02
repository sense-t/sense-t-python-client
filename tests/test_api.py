"""
MIT License
Copyright (c) 2016 Ionata Digital

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
from __future__ import unicode_literals, absolute_import, print_function

import json
import uuid
import datetime

from sensetdp.error import SenseTError
from sensetdp.models import Organisation, Group, Platform, Stream, StreamResultType, StreamMetaData, StreamMetaDataType, \
    InterpolationType, Observation, UnivariateResult
from sensetdp.utils import SenseTEncoder
from tests.config import *
from pprint import pprint

import six
if six.PY3:
    import unittest
    from unittest.case import skip
else:
    import unittest2 as unittest
    from unittest2.case import skip


def dumps(*args, **kwargs):
    if 'cls' not in kwargs:
        kwargs['cls'] = SenseTEncoder
    return json.dumps(*args, **kwargs)


class ApiTestCase(SenseTTestCase):
    existing_platform_id = '05b31a8b-0549-4484-a1b9-a05b89fc677f'
    new_platform_id = 'bdd78502-11bc-4645-9597-0d3231f27212'
    non_existent_stream_id = '0228cefb-8782-4f99-9492-ad3f1febdc12'
    new_stream_id = '21cdbef1f3da-2949-99f4-2878-bfec8220'

    def setUp(self):
        super(ApiTestCase, self).setUp()

    def generate_platform(self):
        o = Organisation()
        o.id = "utas"

        g = Group()
        g.id = "ionata_sandbox"

        p = Platform()
        p.id = "test_platform_{0}".format(self.new_platform_id)
        p.name = "A Platform create for unittests"
        p.organisations = [o]
        p.groups = [g]
        return p

    def generate_stream(self):
        p = self.generate_platform()

        o = Organisation()
        o.id = p.organisations[0].id

        g = Group()
        g.id = p.groups[0].id

        s = Stream()
        s.id = "{0}_location".format(self.new_stream_id)

        s.groups = [g]
        s.organisations = [o]

        s.result_type = StreamResultType.geolocation

        s.samplePeriod = 'PT10S'
        s.reportingPeriod = 'P1D'

        sm = StreamMetaData()
        sm.type = StreamMetaDataType.geolocation
        sm.interpolation_type = InterpolationType.continuous

        s.metadata = sm

        return s, p

    @tape.use_cassette('test_create_platform.json')
    # @skip("Permissions issues")
    def test_create_platform(self):
        """
        Platform creation test, no clean up
        :return: None
        """
        # create
        p = self.generate_platform()

        required_json = dumps({
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
        self.assertEqual(actual_json, required_json)

        created_platform = self.api.create_platform(p)

        # verify
        self.assertEqual(created_platform.id, p.id)
        self.assertEqual(created_platform.name, p.name)

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
        self.assertEqual(updated_platform.name, created_platform.name)

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
        self.assertIsNone(deleted_platform)

    @tape.use_cassette('test_verify_init_stream.json')
    def test_verify_init_stream(self):
        # required
        stream = {}
        stream['id'] = "{0}_location".format(self.existing_platform_id)
        stream['resulttype'] = 'geolocationvalue'
        stream['groupids'] = ['tourtracker']
        stream['samplePeriod'] = 'PT10S'
        stream['reportingPeriod'] = 'P1D'
        stream['organisationid'] = 'utas'
        stream['streamMetadata'] = {
            # 'type': '.GeoLocationStreamMetaData', # type is not used or returned after creation
            'interpolationType': 'http://www.opengis.net/def/waterml/2.0/interpolationType/Continuous',
        }
        required_json = dumps(stream, sort_keys=True)  # be explict with key order since dumps gives us a string

        # get from api
        s = self.api.get_stream(id=stream['id'])
        actual_json = s.to_json("get")

        # verify json
        self.assertEqual(actual_json, required_json)

    @tape.use_cassette('test_non_existent_stream.json')
    def test_non_existent_stream(self):
        stream_nonexistent_id = "{0}_nonexistent".format(self.non_existent_stream_id)
        # stream_exists_id = "{0}_location".format(self.existing_platform_id)

        with self.assertRaises(SenseTError) as arc:
            s = self.api.get_stream(id=stream_nonexistent_id)

        try:
            s = self.api.get_stream(id=stream_nonexistent_id)
        except SenseTError as ex:
            self.assertEqual(ex.api_code, 401)

    @tape.use_cassette('test_create_stream.json')
    def test_create_stream(self):
        s, p = self.generate_stream()

        required_state = {
            "id": s.id,
            "resulttype": "geolocationvalue",
            "organisationid": p.organisations[0].id,
            "groupids": [
                p.groups[0].id
            ],
            "samplePeriod": "PT10S",
            "reportingPeriod": 'P1D',
            "streamMetadata": {
                "type": ".GeoLocationStreamMetaData",
                "interpolationType": "http://www.opengis.net/def/waterml/2.0/interpolationType/Continuous",
            }
        }
        required_json = dumps(required_state, sort_keys=True)  # be explict with key order since dumps gives us a string

        actual_state = s.to_state("create")
        actual_json = s.to_json("create")

        # dict diff
        # from deepdiff import DeepDiff
        # diff = DeepDiff(required_state, actual_state)

        # verify json
        self.assertEqual(actual_json, required_json)

        created_stream = self.api.create_stream(s)

        self.assertEqual(s.id, created_stream.id)

        # verify json
        self.assertEqual(actual_json, required_json)

    @tape.use_cassette('test_create_observations.json')
    def test_create_observations(self):
        s, p = self.generate_stream()

        o = Observation()

        dt = datetime.datetime(2016, 2, 15, 0, 0, 0)
        dt_td = datetime.timedelta(minutes=15)

        points = [
            {'time': dt + (dt_td * 0), "lng": 147.326262, "lat": -42.8840887, 'alt': 50},
            {'time': dt + (dt_td * 1), "lng": 147.3263529, "lat": -42.8844541},  # altitude missing, just because.
            {'time': dt + (dt_td * 2), "lng": 147.3232176, "lat": -42.883477, 'alt': 250},
        ]

        for p in points:
            item = UnivariateResult()
            item.t = p.get('time')
            coords = [p.get('lng'), p.get('lat'), p.get('alt')] if p.get('alt') is not None else [p.get('lng'), p.get('lat')]

            item.v = {
                'p': {
                    'type': 'Point',
                    'coordinates': coords
                }
            }
            o.results.append(item)

        dt_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        required_state = {
            'results': [
                {
                    't':  points[0].get('time').strftime(dt_format),
                    'v': {
                        'p': {
                            'type': 'Point',
                            'coordinates': [points[0].get('lng'), points[0].get('lat'), points[0].get('alt')]
                        }
                    }
                },
                {
                    't':  points[1].get('time').strftime(dt_format),
                    'v': {
                        'p': {
                            'type': 'Point',
                            'coordinates': [points[1].get('lng'), points[1].get('lat')]
                        }
                    }
                },
                {
                    't':  points[2].get('time').strftime(dt_format),
                    'v': {
                        'p': {
                            'type': 'Point',
                            'coordinates': [points[2].get('lng'), points[2].get('lat'), points[2].get('alt')]
                        }
                    }
                },
            ]
        }
        required_json = dumps(required_state, sort_keys=True)  # be explict with key order since dumps gives us a string

        actual_state = o.to_state("create")
        actual_json = o.to_json("create")

        ### dict diff debugging
        # from deepdiff import DeepDiff
        # diff = DeepDiff(required_state, actual_state)

        # verify json
        self.assertEqual(actual_json, required_json)

        created_stream = self.api.create_stream(s)

        self.assertEqual(created_stream.id, s.id)

        created_observation = self.api.create_observations(o, streamid=s.id)

        self.assertEqual(created_observation.get('message'), "Observations uploaded")
        self.assertEqual(created_observation.get('status'), 201)
