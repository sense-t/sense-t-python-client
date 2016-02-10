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

from __future__ import print_function

import time
import re
import six
import requests
import logging

from sensetdp.error import SenseTError, RateLimitError, is_rate_limit_error_message
from sensetdp.utils import convert_to_utf8_str
from sensetdp.models import Model

if six.PY2:
    from urllib import quote
else:
    from urllib.parse import quote


re_path_template = re.compile('{\w+}')

log = logging.getLogger('senset.binder')


def bind_api(**config):

    class APIMethod(object):

        api = config['api']
        path = config['path']
        action = config.get('action', None)
        payload_type = config.get('payload_type', None)
        payload_list = config.get('payload_list', False)
        allowed_param = config.get('allowed_param', [])
        method = config.get('method', 'GET')
        require_auth = config.get('require_auth', False)
        use_cache = config.get('use_cache', True)
        session = requests.Session()

        def __init__(self, args, kwargs):
            api = self.api
            # If authentication is required and no credentials
            # are provided, throw an error.
            if self.require_auth and not api.auth:
                raise SenseTError('Authentication required!')

            self.post_data = kwargs.pop('post_data', None)
            self.json_data = kwargs.pop('json_data', {})
            self.use_json = kwargs.pop('use_json', True)

            self.retry_count = kwargs.pop('retry_count',
                                          api.retry_count)
            self.retry_delay = kwargs.pop('retry_delay',
                                          api.retry_delay)
            self.retry_errors = kwargs.pop('retry_errors',
                                           api.retry_errors)
            self.wait_on_rate_limit = kwargs.pop('wait_on_rate_limit',
                                                 api.wait_on_rate_limit)
            self.wait_on_rate_limit_notify = kwargs.pop('wait_on_rate_limit_notify',
                                                        api.wait_on_rate_limit_notify)
            self.parser = kwargs.pop('parser', api.parser)
            self.session.headers = kwargs.pop('headers', {})
            self.build_parameters(args, kwargs)

            self.api_root = api.api_root

            # Perform any path variable substitution
            self.build_path()

            self.host = api.host

            # TODO: test and remove below.
            # Manually set Host header to fix an issue in python 2.5
            # or older where Host is set including the 443 port.
            # This causes Twitter to issue 301 redirect.
            # See Issue https://github.com/tweepy/tweepy/issues/12
            # self.session.headers['Host'] = self.host

            # Monitoring rate limits
            self._remaining_calls = None
            self._reset_time = None

        def build_parameters(self, args, kwargs):
            if len(args) == 1 and isinstance(args[0], Model):
                kwargs = args[0].__getstate__(self.action)
                args = list()
            else:
                for k, v in kwargs.items():
                    if isinstance(v, Model):
                        kwargs[k] = v.__getstate__(self.action)

            # filter kwargs for allowed_param
            kwargs = dict([(k, v) for k, v in kwargs.items() if k in self.allowed_param])

            if self.use_json:
                self.json_data = dict(**kwargs)

            self.session.params = {}
            for idx, arg in enumerate(args):
                if arg is None:
                    continue
                try:
                    self.session.params[self.allowed_param[idx]] = convert_to_utf8_str(arg)
                except IndexError:
                    raise SenseTError('Too many parameters supplied!')

            for k, arg in kwargs.items():
                if arg is None:
                    continue
                if k in self.session.params:
                    raise SenseTError('Multiple values for parameter %s supplied!' % k)

                self.session.params[k] = convert_to_utf8_str(arg)

            log.info("PARAMS: %r", self.session.params)

        def build_path(self):
            for variable in re_path_template.findall(self.path):
                name = variable.strip('{}')

                if name == 'user' and 'user' not in self.session.params and self.api.auth:
                    # No 'user' parameter provided, fetch it from Auth instead.
                    value = self.api.auth.get_username()
                else:
                    try:
                        value = quote(self.session.params[name])
                    except KeyError:
                        raise SenseTError('No parameter value found for path variable: %s' % name)
                    del self.session.params[name]

                self.path = self.path.replace(variable, value)

        def execute(self):
            self.api.cached_result = False

            # Build the request URL
            url = self.api_root + self.path
            full_url = 'https://' + self.host + url

            # Query the cache if one is available
            # and this request uses a GET method.
            if self.use_cache and self.api.cache and self.method == 'GET':
                cache_result = self.api.cache.get(url)
                # if cache result found and not expired, return it
                if cache_result:
                    # must restore api reference
                    if isinstance(cache_result, list):
                        for result in cache_result:
                            if isinstance(result, Model):
                                result._api = self.api
                    else:
                        if isinstance(cache_result, Model):
                            cache_result._api = self.api
                    self.api.cached_result = True
                    return cache_result

            # Continue attempting request until successful
            # or maximum number of retries is reached.
            retries_performed = 0
            while retries_performed < self.retry_count + 1:
                # handle running out of api calls
                if self.wait_on_rate_limit:
                    if self._reset_time is not None:
                        if self._remaining_calls is not None:
                            if self._remaining_calls < 1:
                                sleep_time = self._reset_time - int(time.time())
                                if sleep_time > 0:
                                    if self.wait_on_rate_limit_notify:
                                        print("Rate limit reached. Sleeping for:", sleep_time)
                                    time.sleep(sleep_time + 5)  # sleep for few extra sec

                # if self.wait_on_rate_limit and self._reset_time is not None and \
                #                 self._remaining_calls is not None and self._remaining_calls < 1:
                #     sleep_time = self._reset_time - int(time.time())
                #     if sleep_time > 0:
                #         if self.wait_on_rate_limit_notify:
                #             print("Rate limit reached. Sleeping for: " + str(sleep_time))
                #         time.sleep(sleep_time + 5)  # sleep for few extra sec

                # Apply authentication
                if self.api.auth:
                    auth = self.api.auth.apply_auth()

                # Request compression if configured
                if self.api.compression:
                    self.session.headers['Accept-encoding'] = 'gzip'

                # Execute request
                try:
                    if self.use_json:
                        resp = self.session.request(self.method,
                                                    full_url,
                                                    json=self.json_data,
                                                    timeout=self.api.timeout,
                                                    auth=auth,
                                                    proxies=self.api.proxy)
                    else:
                        resp = self.session.request(self.method,
                                                    full_url,
                                                    data=self.post_data,
                                                    timeout=self.api.timeout,
                                                    auth=auth,
                                                    proxies=self.api.proxy)
                except Exception as e:
                    raise SenseTError('Failed to send request: %s' % e)
                rem_calls = resp.headers.get('x-rate-limit-remaining')
                if rem_calls is not None:
                    self._remaining_calls = int(rem_calls)
                elif isinstance(self._remaining_calls, int):
                    self._remaining_calls -= 1
                reset_time = resp.headers.get('x-rate-limit-reset')
                if reset_time is not None:
                    self._reset_time = int(reset_time)
                if self.wait_on_rate_limit and self._remaining_calls == 0 and (
                        # if ran out of calls before waiting switching retry last call
                                resp.status_code == 429 or resp.status_code == 420):
                    continue
                retry_delay = self.retry_delay
                # Exit request loop if non-retry error code
                if resp.status_code == 200:
                    break
                elif (resp.status_code == 429 or resp.status_code == 420) and self.wait_on_rate_limit:
                    if 'retry-after' in resp.headers:
                        retry_delay = float(resp.headers['retry-after'])
                elif self.retry_errors and resp.status_code not in self.retry_errors:
                    break

                # Sleep before retrying request again
                time.sleep(retry_delay)
                retries_performed += 1

            # If an error was returned, throw an exception
            self.api.last_response = resp
            if resp.status_code and not 200 <= resp.status_code < 300:
                try:
                    error_msg, api_error_code = \
                        self.parser.parse_error(resp.text)
                except Exception:
                    error_msg = "SenseT error response: status code = %s" % resp.status_code
                    api_error_code = None

                if is_rate_limit_error_message(error_msg):
                    raise RateLimitError(error_msg, resp)
                else:
                    raise SenseTError(error_msg, resp, api_code=api_error_code)

            # Parse the response payload
            result = self.parser.parse(self, resp.text)

            # Store result into cache if one is available.
            if self.use_cache and self.api.cache and self.method == 'GET' and result:
                self.api.cache.store(url, result)

            return result

    def _call(*args, **kwargs):
        method = APIMethod(args, kwargs)
        if kwargs.get('create'):
            return method
        else:
            return method.execute()

    # Set pagination mode
    if 'cursor' in APIMethod.allowed_param:
        _call.pagination_mode = 'cursor'
    elif 'max_id' in APIMethod.allowed_param:
        if 'since_id' in APIMethod.allowed_param:
            _call.pagination_mode = 'id'
    elif 'page' in APIMethod.allowed_param:
        _call.pagination_mode = 'page'

    return _call
