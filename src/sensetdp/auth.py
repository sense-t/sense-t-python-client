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
from requests.auth import _basic_auth_str


class AuthBase(object):
    """Base class that all auth implementations derive from"""

    def __call__(self, r):
        raise NotImplementedError('Auth hooks must be callable.')

    def get_username(self):
        raise NotImplementedError('Auth get_username() must be implemented.')

    def apply_auth(self):
        raise NotImplementedError('Auth apply_auth() must be implemented.')


class HTTPBasicAuth(AuthBase):
    """Attaches HTTP Basic Authentication to the given Request object."""

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __call__(self, r):
        r.headers['Authorization'] = _basic_auth_str(self.username, self.password)
        return r

    def get_username(self):
        return self.username

    def apply_auth(self):
        return self


class HTTPKeyAuth(AuthBase):
    """
    Attaches an API key to the given Request object.
    
    NOTE: as the corresponding username is unknown, using this auth scheme will
    break the api.me() method.
    
    TODO: figure out if there's a way to support API keys in query parameters
    instead of headers.
    """
    
    def __init__(self, key, header='apikey'):
        self.key = key
        self.header = header
    
    def __call__(self, r):
        r.headers[self.header] = self.key
        return r
    
    def apply_auth(self):
        return self
