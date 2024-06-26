#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# checkmk_dell_rackpdu - Checkmk extension for Dell Rack PDUs
#
# Copyright (C) 2021-2024  Marius Rieder <marius.rieder@durchmesser.ch>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import pytest  # type: ignore[import]
from cmk.agent_based.v2 import (
    Metric,
    Result,
    Service,
    State,
)
from cmk_addons.plugins.dell_rackpdu.agent_based import dell_rackpdu_sensor_humidity


@pytest.mark.parametrize('string_table, result', [
    (
        [[], []], {}
    ),
    (
        [[['SensorName', '10', '0']], [['SensorName', '28', '4']]],
        {'SensorName': [28, 4, 10, 0]}
    ),
])
def test_parse_dell_rackpdu_sensor_humidity(string_table, result):
    assert dell_rackpdu_sensor_humidity.parse_dell_rackpdu_sensor_humidity(string_table) == result


@pytest.mark.parametrize('section, result', [
    ({}, []),
    (
        {'SensorName': [28, 4, 10, 0]},
        [Service(item='SensorName')]
    )
])
def test_discovery_dell_rackpdu_sensor_humidity(section, result):
    assert list(dell_rackpdu_sensor_humidity.discovery_dell_rackpdu_sensor_humidity(section)) == result


@pytest.mark.parametrize('item, params, section, result', [
    ('', {}, {}, []),
    (
        'foo', {},
        {'SensorName': [28, 4, 10, 0]},
        []
    ),
    (
        'SensorName', {},
        {'SensorName': [28, 4, 10, 0]},
        [
            Result(state=State.OK, summary='28.00%'),
            Metric('humidity', 28.0)
        ]
    ),
    (
        'SensorName', {'levels_lower': ('fixed', (30, 20))},
        {'SensorName': [28, 4, 10, 0]},
        [
            Result(state=State.WARN, summary='28.00% (warn/crit below 30.00%/20.00%)'),
            Metric('humidity', 28.0)
        ]
    ),
    (
        'SensorName', {'levels_lower': ('fixed', (30, 29))},
        {'SensorName': [28, 4, 10, 0]},
        [
            Result(state=State.CRIT, summary='28.00% (warn/crit below 30.00%/29.00%)'),
            Metric('humidity', 28.0)
        ]
    ),
    (
        'SensorName', {'levels': ('fixed', (20, 30))},
        {'SensorName': [28, 4, 10, 0]},
        [
            Result(state=State.WARN, summary='28.00% (warn/crit at 20.00%/30.00%)'),
            Metric('humidity', 28.0, levels=(20.0, 30.0))
        ]
    ),
    (
        'SensorName', {'levels': ('fixed', (20, 25))},
        {'SensorName': [28, 4, 10, 0]},
        [
            Result(state=State.CRIT, summary='28.00% (warn/crit at 20.00%/25.00%)'),
            Metric('humidity', 28.0, levels=(20.0, 25.0))
        ]
    ),
])
def test_check_dell_rackpdu_sensor_humidity(item, params, section, result):
    assert list(dell_rackpdu_sensor_humidity.check_dell_rackpdu_sensor_humidity(item, params, section)) == result
