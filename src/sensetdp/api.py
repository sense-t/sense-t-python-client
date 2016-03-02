"""
MIT License
Copyright (c) 2016 Ionata Digital
Copyright (c) 2009-2014 Joshua Roesslein

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

from sensetdp.binder import bind_api
from sensetdp.error import SenseTError
from sensetdp.parsers import ModelParser, Parser
from sensetdp.utils import list_to_csv


class API(object):
    """Sense-T API"""
    def __init__(self, auth_handler=None,
                 host='data.sense-t.org.au', cache=None, api_root='/api/sensor/v2',
                 retry_count=0, retry_delay=0, retry_errors=None, timeout=60, parser=None,
                 compression=False, wait_on_rate_limit=False,
                 wait_on_rate_limit_notify=False, proxy=''):
        """ Api instance Constructor

        :param auth_handler:
        :param host:  url of the server of the rest api, default:'api.twitter.com'
        :param cache: Cache to query if a GET method is used, default:None
        :param api_root: suffix of the api version, default:'/1.1'
        :param retry_count: number of allowed retries, default:0
        :param retry_delay: delay in second between retries, default:0
        :param retry_errors: default:None
        :param timeout: delay before to consider the request as timed out in seconds, default:60
        :param parser: ModelParser instance to parse the responses, default:None
        :param compression: If the response is compressed, default:False
        :param wait_on_rate_limit: If the api wait when it hits the rate limit, default:False
        :param wait_on_rate_limit_notify: If the api print a notification when the rate limit is hit, default:False
        :param proxy: Url to use as proxy during the HTTP request, default:''

        :raise TypeError: If the given parser is not a ModelParser instance.
        """
        self.auth = auth_handler
        self.host = host
        self.api_root = api_root
        self.cache = cache
        self.compression = compression
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.retry_errors = retry_errors
        self.timeout = timeout
        self.wait_on_rate_limit = wait_on_rate_limit
        self.wait_on_rate_limit_notify = wait_on_rate_limit_notify
        self.parser = parser or ModelParser()
        self.proxy = {}
        if proxy:
            self.proxy['https'] = proxy

        parser_type = Parser
        if not isinstance(self.parser, parser_type):
            raise TypeError(
                '"parser" argument has to be an instance of "{required}".'
                ' It is currently a {actual}.'.format(
                    required=parser_type.__name__,
                    actual=type(self.parser)
                )
            )

    def me(self):
        """ Get the authenticated user """
        return self.get_user(userid=self.auth.get_username())

    @property
    def get_user(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/get_users_userid
            :allowed_param: 'userid'
        """
        return bind_api(
            api=self,
            path='/users/{userid}',
            payload_type='user',
            allowed_param=['userid'],
            require_auth=True,
        )

    @property
    def platforms(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/put_platforms_id
        """
        return bind_api(
            api=self,
            path='/platforms',
            payload_type='platform',
            payload_list=True,
            require_auth=True,
        )

    @property
    def create_platform(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/put_platforms_id
            :allowed_param: 'id', 'name', 'organisationid', 'groupids', 'streamids', 'deployments'
        """
        return bind_api(
            api=self,
            path='/platforms/{id}',
            method='PUT',
            payload_type='platform',
            action='create',
            allowed_param=[
                'id',
                'name',
                'organisationid',
                'groupids',
                'streamids',
                'deployments',
            ],
            require_auth=True,
        )

    @property
    def update_platform(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/put_platforms_id
            :allowed_param: 'id', 'name', 'organisationid', 'groupids', 'streamids', 'deployments',
        """
        return bind_api(
            api=self,
            path='/platforms/{id}',
            method='PUT',
            payload_type='platform',
            action='update',
            allowed_param=[
                'id',
                'name',
                'organisationid',
                'groupids',
                'streamids',
                'deployments',
            ],
            require_auth=True,
        )

    @property
    def destroy_platform(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/delete_platforms_id
            :allowed_param: 'id', 'cascade'
        """
        return bind_api(
            api=self,
            path='/platforms/{id}',
            method='DELETE',
            payload_type='platform',
            allowed_param=[
                'id',
                'cascade',
            ],
            require_auth=True,
        )

    @property
    def get_stream(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/get_streams_id
            :allowed_param: 'id'
        """
        return bind_api(
            api=self,
            path='/streams/{id}',
            method='GET',
            payload_type='stream',
            allowed_param=['id'],
            require_auth=True,
        )

    @property
    def create_stream(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/put_streams_id
            :allowed_param: 'id', 'resulttype', 'organisationid', 'groupids', 'procedureid', 'samplePeriod',
            'reportingPeriod', 'streamMetadata',
        """
        return bind_api(
            api=self,
            path='/streams/{id}',
            method='PUT',
            payload_type='stream',
            action='create',
            allowed_param=[
                'id',
                'resulttype',
                'organisationid',
                'groupids',
                'procedureid',
                'samplePeriod',
                'reportingPeriod',
                'streamMetadata',
            ],
            require_auth=True,
        )

    @property
    def update_stream(self):
        return self.create_stream

    @property
    def destroy_stream(self):
        pass

    @property
    def create_observations(self):
        """ :reference: https://data.sense-t.org.au/api/sensor/v2/api-docs/#!/default/post_observations
            :allowed_param: 'streamid', 'results'
        """
        return bind_api(
            api=self,
            path='/observations',
            method='POST',
            payload_type='json',
            action='create',
            allowed_param=[
                'streamid',
                'results',
            ],
            query_only_param=[
                'streamid',
            ],
            require_auth=True,
        )
