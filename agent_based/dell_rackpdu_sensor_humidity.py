#!/usr/bin/env python3
# # -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# checkmk_dell_rackpdu - Checkmk extension for Dell Rack PDUs
#
# Copyright (C) 2021  Marius Rieder <marius.rieder@scs.ch>
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

# .1.3.6.1.4.1.674.10903.200.2.200.150.3.2.1.1.1 1 --> DellrPDU-MIB::rPDUSensorHumidityStatusIndex.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.2.1.2.1 SensorName --> DellrPDU-MIB::rPDUSensorHumidityStatusName.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.2.1.3.1 2 --> DellrPDU-MIB::rPDUSnsorHumidityStatCommStatus.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.2.1.4.1 28 --> DellrPDU-MIB::rPDUSnsorHumStatRelativeHumdity.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.2.1.5.1 4 --> DellrPDU-MIB::rPDUSnsorHumStatusAlarmStatus.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1.1.1 1 --> DellrPDU-MIB::rPDUSensorHumidityConfigIndex.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1.2.1 SensorName --> DellrPDU-MIB::rPDUSensorHumidityConfigName.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1.3.1 10 --> DellrPDU-MIB::rPDUSnsorHumCfgHumdityLowThresh.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1.4.1 0 --> DellrPDU-MIB::rPDUSnsorHumCfgHumdityMinThresh.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1.5.1 1 --> DellrPDU-MIB::rPDUSnsorHumCfgHumdtyHysteresis.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1.6.1 2 --> DellrPDU-MIB::rPDUSnsorHumCfgAlarmGeneration.1


from .agent_based_api.v1 import (
    all_of,
    check_levels,
    exists,
    register,
    render,
    Result,
    Service,
    SNMPTree,
    startswith,
    State,
)

DELL_RACKPDU_SENSOR_LEVEL_STATES = {
    1: State.CRIT,  # not present
    2: State.CRIT,  # low critical,
    3: State.WARN,  # low warning,
    4: State.OK,    # normal,
    5: State.WARN,  # high warning,
    6: State.CRIT,  # high critical,
}


def parse_dell_rackpdu_sensor_humidity(string_table):
    parsed = {}

    sensor_config, sensor_status = string_table
    for name, humidity, status in sensor_status:
        parsed[name] = [
            int(humidity),  # humidity
            int(status)     # status
        ]
    for name, warning, critical in sensor_config:
        parsed[name].extend([
            int(warning),  # warning
            int(critical)  # critical
        ])
    return parsed


register.snmp_section(
    name='dell_rackpdu_sensor_humidity',
    detect=all_of(
        startswith('.1.3.6.1.2.1.1.1.0', 'DELL Web/SNMP'),
        exists('.1.3.6.1.4.1.674.10903.200.2.200.150.3.*')
    ),
    parse_function=parse_dell_rackpdu_sensor_humidity,
    fetch=[
        SNMPTree(
            base='.1.3.6.1.4.1.674.10903.200.2.200.150.3.3.1',
            oids=[
                '2',  # DellrPDU-MIB::rPDUSensorHumidityConfigName
                '3',  # DellrPDU-MIB::rPDUSnsorHumCfgHumdityLowThresh
                '4',  # DellrPDU-MIB::rPDUSnsorHumCfgHumdityMinThresh
            ]),
        SNMPTree(
            base='.1.3.6.1.4.1.674.10903.200.2.200.150.3.2.1',
            oids=[
                '2',  # DellrPDU-MIB::rPDUSensorHumidityStatusName
                '4',  # DellrPDU-MIB::rPDUSnsorHumStatRelativeHumdity
                '5',  # DellrPDU-MIB::rPDUSensorTempStatusAlarmStatus
            ]),
    ],
)


def discovery_dell_rackpdu_sensor_humidity(section):
    for sensor in section.keys():
        if section[sensor][1] == 1:
            continue
        yield Service(item=sensor)


def check_dell_rackpdu_sensor_humidity(item, params, section):
    if item not in section:
        yield Result(state=State.UNKNOWN, summary='Sensor %s not found.' % item)
        return

    humidity, status, warn, crit = section[item]

    yield from check_levels(
        value=humidity,
        metric_name='humidity',
        levels_upper=params.get('levels', None),
        levels_lower=params.get('levels_lower', (warn, crit)),
        render_func=render.percent,
    )


register.check_plugin(
    name='dell_rackpdu_sensor_humidity',
    service_name='%s Humidity',
    discovery_function=discovery_dell_rackpdu_sensor_humidity,
    check_function=check_dell_rackpdu_sensor_humidity,
    check_default_parameters={},
    check_ruleset_name='humidity',
)
