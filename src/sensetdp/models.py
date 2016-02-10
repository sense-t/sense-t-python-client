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

import json

import enum

from sensetdp.error import SenseTError


class StreamResultType(enum.Enum):
    scalar = "scalarvalue"
    geolocation = "geolocationvalue"


class StreamMetaDataType(enum.Enum):
    scalar = ".ScalarStreamMetaData"
    geolocation = ".GeoLocationStreamMetaData"


class InterpolationType(enum.Enum):
    Continuous = 'http://www.opengis.net/def/waterml/2.0/interpolationType/Continuous'
    Discontinuous = 'http://www.opengis.net/def/waterml/2.0/interpolationType/Discontinuous'
    InstantTotal = 'http://www.opengis.net/def/waterml/2.0/interpolationType/InstantTotal'
    AveragePrec = 'http://www.opengis.net/def/waterml/2.0/interpolationType/AveragePrec'
    MaxPrec = 'http://www.opengis.net/def/waterml/2.0/interpolationType/MaxPrec'
    MinPrec = 'http://www.opengis.net/def/waterml/2.0/interpolationType/MinPrec'
    TotalPrec = 'http://www.opengis.net/def/waterml/2.0/interpolationType/TotalPrec'
    ConstPrec = 'http://www.opengis.net/def/waterml/2.0/interpolationType/ConstPrec'
    AverageSucc = 'http://www.opengis.net/def/waterml/2.0/interpolationType/AverageSucc'
    TotalSucc = 'http://www.opengis.net/def/waterml/2.0/interpolationType/TotalSucc'
    MinSucc = 'http://www.opengis.net/def/waterml/2.0/interpolationType/MinSucc'
    MaxSucc = 'http://www.opengis.net/def/waterml/2.0/interpolationType/MaxSucc'
    ConstSucc = 'http://www.opengis.net/def/waterml/2.0/interpolationType/ConstSucc'


class ResultSet(list):
    """A list like object that holds results from a Twitter API query."""
    def __init__(self, max_id=None, since_id=None):
        super(ResultSet, self).__init__()
        self._max_id = max_id
        self._since_id = since_id

    @property
    def max_id(self):
        if self._max_id:
            return self._max_id
        ids = self.ids()
        # Max_id is always set to the *smallest* id, minus one, in the set
        return (min(ids) - 1) if ids else None

    @property
    def since_id(self):
        if self._since_id:
            return self._since_id
        ids = self.ids()
        # Since_id is always set to the *greatest* id in the set
        return max(ids) if ids else None

    def ids(self):
        return [item.id for item in self if hasattr(item, 'id')]


class Model(object):

    def __init__(self, api=None):
        self._api = api

    def __getstate__(self, action=None):
        # pickle
        pickle = dict(self.__dict__)
        try:
            for key in [k for k in pickle.keys() if k.startswith('_')]:
                del pickle[key]  # do not pickle private attrs
        except KeyError:
            pass

        # allow model implementations to mangle state on different api actions
        action_fn = getattr(self, "__getstate_{0}__".format(action), None)
        if action and callable(action_fn):
            pickle = action_fn(pickle)

        return pickle

    def to_json(self, action=None):
        return json.dumps(self.__getstate__(action), sort_keys=True)  # be explict with key order so unittest work.

    @classmethod
    def parse(cls, api, json):
        """Parse a JSON object into a model instance."""
        raise NotImplementedError

    @classmethod
    def parse_list(cls, api, json_list):
        """
            Parse a list of JSON objects into
            a result set of model instances.
        """
        results = ResultSet()
        for obj in json_list:
            if obj:
                results.append(cls.parse(api, obj))
        return results

    def __repr__(self):
        state = ['%s=%s' % (k, repr(v)) for (k, v) in vars(self).items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(state))


class Platform(Model):
    def __init__(self, api=None):
        super(Platform, self).__init__(api=api)
        self._organisations = list()
        self._groups = list()
        self._streams = list()
        self._deployments = list()

    def __getstate__(self, action=None):
        pickled = super(Platform, self).__getstate__(action)

        pickled["groupids"] = [g.id for g in self.groups]
        pickled["streamids"] = [s.id for s in self.streams]
        pickled["deployments"] = [d.__getstate__(action) for d in self.deployments]
        return pickled

    def __getstate_create__(self, pickled):
        """
        :param pickled: dict of object kay, values
        :return: API weirdly requires a single organisationid on creation/update but returns a list
        """
        if not self.organisations:
            raise SenseTError("Platform creation requires an organisationid")
        pickled["organisationid"] = self.organisations[0].id
        return pickled

    def __getstate_update__(self, pickled):
        """
        :param pickled: dict of object kay, values
        :return: pointer to self.__getstate_create__
        """
        return self.__getstate_create__(pickled)

    @classmethod
    def parse(cls, api, json):
        platform = cls(api)
        setattr(platform, '_json', json)
        for k, v in json.items():
            if k == "_embedded":
                for ek, ev in v.items():
                    if ek == "organisation":
                        setattr(platform, "organisations", Organisation.parse_list(api, ev))
                    elif ek == "groups":
                        setattr(platform, "groups", Group.parse_list(api, ev))
                    elif ek == "deployments":
                        setattr(platform, "deployments", Deployment.parse_list(api, ev))
            else:
                setattr(platform, k, v)
        return platform

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['platforms']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    @property
    def organisations(self):
        return self._organisations

    @organisations.setter
    def organisations(self, value):
        self._organisations = value

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value

    @property
    def streams(self):
        return self._streams

    @streams.setter
    def streams(self, value):
        self._streams = value

    @property
    def deployments(self):
        return self._deployments

    @deployments.setter
    def deployments(self, value):
        self._deployments = value


class Organisation(Model):
    @classmethod
    def parse(cls, api, json):
        organisation = cls(api)
        setattr(organisation, '_json', json)
        for k, v in json.items():
            setattr(organisation, k, v)
        return organisation

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['organisations']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    def permissions(self):
        raise NotImplementedError("Not implemented")


class Vocabulary(Model):
    pass


class StreamMetaData(Model):
    def __init__(self, api=None):
        super(StreamMetaData, self).__init__(api=api)
        self._api = api
        self._type = None
        self._interpolation_type = None

        # scalar only attrs
        self.observedProperty = None
        self.cummulative = None

        # geo only attrs
        self.unitOfMeasure = None

        # cumulative only attrs
        self.accumulationInterval = None
        self.accumulationAnchor = None

        # required for cumulative scalar streams
        self.timezone = None

    def __getstate__(self, action=None):
        pickled = super(StreamMetaData, self).__getstate__(action)
        pickled["interpolationType"] = self.interpolation_type.value

        if action != "create":
            # purge the type, it is never returned on get request
            try:
                del pickled['type']
            except KeyError:
                pass

        return pickled

    def __getstate_create__(self, pickled):
        """
        :param pickled: dict of object kay, values
        :return:
        """
        if not self.type:
            raise SenseTError("Stream creation requires an type")
        if self.type is not None:
            pickled["type"] = self._type.value
        return pickled

    @classmethod
    def parse(cls, api, json):
        stream_meta_data = cls(api)
        setattr(stream_meta_data, '_json', json)
        for k, v in json.items():
            if k == "_embedded":
                for ek, ev in v.items():
                    if ek == "interpolationType":
                        ev = ev[0].get('_links', {}).get('self', {}).get('href', )
                        setattr(stream_meta_data, "interpolation_type", InterpolationType(ev))
            else:
                setattr(stream_meta_data, k, v)
        return stream_meta_data

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def interpolation_type(self):
        return self._interpolation_type

    @interpolation_type.setter
    def interpolation_type(self, value):
        self._interpolation_type = value


class Stream(Model):
    def __init__(self, api=None):
        super(Stream, self).__init__(api=api)
        self._type = None
        self._organisations = list()
        self._groups = list()
        self._metadata = None

    def __getstate__(self, action=None):
        pickled = super(Stream, self).__getstate__(action)

        pickled["groupids"] = [g.id for g in self.groups]
        pickled["streamMetadata"] = self.metadata.__getstate__(action)
        pickled["organisationid"] = self.organisations[0].id
        return pickled

    @classmethod
    def parse(cls, api, json):
        stream = cls(api)
        setattr(stream, '_json', json)
        for k, v in json.items():
            if k == "resulttype":
                setattr(stream, k, StreamResultType(v))
            if k == "_embedded":
                for ek, ev in v.items():
                    if ek == "organisation":
                        setattr(stream, "organisations", Organisation.parse_list(api, ev))
                    elif ek == "groups":
                        setattr(stream, "groups", Group.parse_list(api, ev))
                    elif ek == "metadata":
                        # metadata is also a list ?????
                        setattr(stream, "metadata", StreamMetaData.parse(api, ev[0]))
            else:
                setattr(stream, k, v)
        return stream

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['streams']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    @property
    def organisations(self):
        return self._organisations

    @organisations.setter
    def organisations(self, value):
        self._organisations = value

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value


class Group(Model):
    @classmethod
    def parse(cls, api, json):
        group = cls(api)
        setattr(group, '_json', json)
        for k, v in json.items():
            setattr(group, k, v)
        return group


class Location(Model):
    pass


class Procedure(Model):
    pass


class Observation(Model):
    pass


class Aggregation(Model):
    pass


class Deployment(Model):
    @classmethod
    def parse(cls, api, json):
        role = cls(api)
        setattr(role, '_json', json)
        for k, v in json.items():
            setattr(role, k, v)
        return role

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['deployments']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    def permissions(self):
        raise NotImplementedError("Not implemented")


class Role(Model):

    @classmethod
    def parse(cls, api, json):
        role = cls(api)
        setattr(role, '_json', json)
        for k, v in json.items():
            setattr(role, k, v)
        return role

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['roles']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    def permissions(self):
        raise NotImplementedError("Not implemented")


class User(Model):

    @classmethod
    def parse(cls, api, json):
        user = cls(api)
        attrs = [
            'id',
            '_links',
            '_embedded',
        ]
        setattr(user, '_json', json)
        for k, v in json.items():
            if k in attrs:
                setattr(user, k, v)
        return user

    @classmethod
    def parse_list(cls, api, json_list):
        if isinstance(json_list, list):
            item_list = json_list
        else:
            item_list = json_list['users']

        results = ResultSet()
        for obj in item_list:
            results.append(cls.parse(api, obj))
        return results

    @property
    def roles(self):
        if hasattr(self, '_embedded') and 'roles' in self._embedded.keys():
            return Role.parse_list(self._api, self._embedded.get('roles'))
        return None

    def groups(self):
        pass


class JSONModel(Model):

    @classmethod
    def parse(cls, api, json):
        return json


class ModelFactory(object):
    """
    Used by parsers for creating instances
    of models. You may subclass this factory
    to add your own extended models.
    """
    user = User
    organisation = Organisation
    group = Group
    role = Role
    vocabulary = Vocabulary
    stream = Stream
    platform = Platform
    location = Location
    procedure = Procedure
    observation = Observation
    aggregation = Aggregation

    json = JSONModel
