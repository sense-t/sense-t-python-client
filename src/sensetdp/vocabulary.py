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

import enum

from sensetdp.error import SenseTError

"""
Vocabulary util functions
"""


def find_observed_property(prop):
    for t in property_types:
        for member in t:
            if member.value == prop:
                return member
    raise SenseTError("Observed property not found.")


def find_unit_of_measurement(unit):
    for t in unit_types:
        for member in t:
            if member.value == unit:
                return member
    raise SenseTError("Unit of measurement not found.")


"""
Observed properties enums
"""


class SenseTObservedProperty(enum.Enum):
    """
    TODO: Generate from a resource file
    http://data.sense-t.org.au/registry/def/sop
    """
    android_battery_status = "http://data.sense-t.org.au/registry/def/sop/AndroidBatteryStatus"
    data_transmitted = "http://data.sense-t.org.au/registry/def/sop/DataTransmitted"
    true_bearing = "http://data.sense-t.org.au/registry/def/sop/TrueBearing"
    battery_state_of_charge = "http://data.sense-t.org.au/registry/def/sop/BatteryStateOfCharge"
    data_received = "http://data.sense-t.org.au/registry/def/sop/DataReceived"
    location_accuracy_radius = "http://data.sense-t.org.au/registry/def/sop/LocationAccuracy"


class QUDTObservedProperty(enum.Enum):
    """
    TODO: Generate from a resource file
    http://registry.it.csiro.au/def/qudt/1.1/_qudt-quantity
    """
    speed = "http://registry.it.csiro.au/def/qudt/1.1/qudt-quantity/Speed"

property_types = [
    SenseTObservedProperty,
    QUDTObservedProperty,
]


"""
Units of measurement enums
"""


class CSIROQUDTUnit(enum.Enum):
    """
    TODO: Generate from a resource file
    http://registry.it.csiro.au/def/qudt/1.1/_qudt-unit
    """
    percent = "http://registry.it.csiro.au/def/qudt/1.1/qudt-unit/Percent"
    unitless = "http://registry.it.csiro.au/def/qudt/1.1/qudt-unit/Unitless"
    byte = "http://registry.it.csiro.au/def/qudt/1.1/qudt-unit/Byte"
    meter = "http://registry.it.csiro.au/def/qudt/1.1/qudt-unit/Meter"
    degree_angle = "http://registry.it.csiro.au/def/qudt/1.1/qudt-unit/DegreeAngle"


class SenseTUnit(enum.Enum):
    """
    TODO: Generate from a resource file
    http://data.sense-t.org.au/registry/def/_su
    """
    kilometres_per_hour = "http://data.sense-t.org.au/registry/def/su/KilometresPerHour"
    hectopascal = "http://data.sense-t.org.au/registry/def/su/HectoPascal"


unit_types = [
    CSIROQUDTUnit,
    SenseTUnit,
]
