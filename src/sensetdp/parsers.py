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

from __future__ import print_function, unicode_literals, absolute_import

from sensetdp.models import ModelFactory
from sensetdp.utils import import_simplejson
from sensetdp.error import SenseTError

from cStringIO import StringIO

class Parser(object):

    def parse(self, method, payload):
        """
        Parse the response payload and return the result.
        Returns a tuple that contains the result data and the cursors
        (or None if not present).
        """
        raise NotImplementedError

    def parse_error(self, payload):
        """
        Parse the error message and api error code from payload.
        Return them as an (error_msg, error_code) tuple. If unable to parse the
        message, throw an exception and default error message will be used.
        """
        raise NotImplementedError


class RawParser(Parser):

    def __init__(self):
        pass

    def parse(self, method, payload):
        return payload

    def parse_error(self, payload):
        return payload


class JSONParser(Parser):

    payload_format = 'json'

    def __init__(self):
        self.json_lib = import_simplejson()

    def parse(self, method, payload):
        try:
            json = self.json_lib.loads(payload)
        except Exception as e:
            raise SenseTError('Failed to parse JSON payload: %s' % e)

        needs_cursors = 'cursor' in method.session.params
        if needs_cursors and isinstance(json, dict):
            if 'previous_cursor' in json:
                if 'next_cursor' in json:
                    cursors = json['previous_cursor'], json['next_cursor']
                    return json, cursors
        else:
            return json

    def parse_error(self, payload):
        error_object = self.json_lib.loads(payload)
        reason = "An unknown error occurred"
        api_code = None

        if 'status' in error_object or 'message' in error_object:
            reason = error_object.get('message', reason)
            api_code = error_object.get('status', None)

        return reason, api_code


class ModelParser(JSONParser):

    def __init__(self, model_factory=None):
        JSONParser.__init__(self)
        self.model_factory = model_factory or ModelFactory

    def parse(self, method, payload):
        try:
            if method.payload_type is None:
                return
            model = getattr(self.model_factory, method.payload_type)
        except AttributeError:
            raise SenseTError('No model for this payload type: '
                             '%s' % method.payload_type)

        json = JSONParser.parse(self, method, payload)
        if isinstance(json, tuple):
            json, cursors = json
        else:
            cursors = None

        if method.payload_list:
            result = model.parse_list(method.api, json)
        else:
            result = model.parse(method.api, json)

        if cursors:
            return result, cursors
        else:
            return result

class PandasObservationParser(Parser):
    def __init__(self):
        import pandas # NOTE: import here means we don't require pandas to be installed unless we actually instantiate this class.
        self.pandas = pandas
        
        self.json_lib = import_simplejson()
    
    def parse(self, method, payload):
		# Validate media type.
        media_type = method.query_params.get('media', None)
        if media_type != 'csv':
            raise SenseTError('PandasObservationParser requires CSV media type (media type "{}" is not supported).'.format(media_type))
        
        # Skip header information.
        stream_ids = method.query_params['streamid'].split(',') # NOTE: this WILL break if stream IDs contain commas (need to properly parse as CSV).
        column_headers = frozenset(['timestamp'] + stream_ids)
        lines = payload.splitlines()
        for i, row in enumerate(lines):
            if set(s.strip() for s in row.split(',')) == column_headers:
                break
        
        # Parse CSV payload.
        df = self.pandas.read_csv(StringIO('\n'.join(lines[i:])), parse_dates=True, index_col='timestamp')
        
        # SensorCloud returns columns in random (alphabetic?) order - reorder to
        # match the order the stream IDs were originally given in.
        if len(stream_ids) > 1:
            df = df[stream_ids]
        
        return df
    
    def parse_error(self, payload):
        error_object = self.json_lib.loads(payload)
        reason = "An unknown error occurred"
        api_code = None
        
        if 'status' in error_object or 'message' in error_object:
            reason = error_object.get('message', reason)
            api_code = error_object.get('status', None)
        
        return reason, api_code
