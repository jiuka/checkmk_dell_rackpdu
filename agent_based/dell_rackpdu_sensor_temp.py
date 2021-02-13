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

# .1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1.1.1 1 --> DellrPDU-MIB::rPDUSensorTempStatusIndex.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1.2.1 SensorName --> DellrPDU-MIB::rPDUSensorTempStatusName.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1.3.1 2 --> DellrPDU-MIB::rPDUSensorTempStatusCommStatus.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1.4.1 759 --> DellrPDU-MIB::rPDUSensorTempStatusTempF.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1.5.1 244 --> DellrPDU-MIB::rPDUSensorTempStatusTempC.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1.6.1 4 --> DellrPDU-MIB::rPDUSensorTempStatusAlarmStatus.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.1.1 1 --> DellrPDU-MIB::rPDUSensorTempConfigIndex.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.2.1 SensorName --> DellrPDU-MIB::rPDUSensorTempConfigName.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.3.1 140 --> DellrPDU-MIB::rPDUSensorTempCfgTempMaxThreshF.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.4.1 138 --> DellrPDU-MIB::rPDUSnsorTempCfgTempHighThreshF.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.5.1 2 --> DellrPDU-MIB::rPDUSnsorTempCfgTempHysteresisF.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.6.1 60 --> DellrPDU-MIB::rPDUSensorTempCfgTempMaxThreshC.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.7.1 59 --> DellrPDU-MIB::rPDUSnsorTempCfgTempHighThreshC.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.8.1 1 --> DellrPDU-MIB::rPDUSnsorTempCfgTempHysteresisC.1
# .1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1.9.1 2 --> DellrPDU-MIB::rPDUSnsorTempCfgAlarmGeneration.1

from .agent_based_api.v1 import (
    all_of,
    exists,
    register,
    Service,
    SNMPTree,
    startswith,
    State,
)
from .utils.temperature import (
    check_temperature,
)

DELL_RACKPDU_SENSOR_LEVEL_STATES = {
    1: State.CRIT,  # not present
    2: State.CRIT,  # low critical,
    3: State.WARN,  # low warning,
    4: State.OK,    # normal,
    5: State.WARN,  # high warning,
    6: State.CRIT,  # high critical,
}


def parse_dell_rackpdu_sensor_temp(string_table):
    parsed = {}
    sensor_config, sensor_status = string_table
    for name, temperature, status in sensor_status:
        parsed[name] = [
            int(temperature) / 10.0,  # temparature
            int(status)               # status
        ]
    for name, warning, critical in sensor_config:
        parsed[name].extend([
            int(warning),  # warning
            int(critical)  # critical
        ])
    return parsed


register.snmp_section(
    name='dell_rackpdu_sensor_temp',
    detect=all_of(
        startswith('.1.3.6.1.2.1.1.1.0', 'DELL Web/SNMP'),
        exists('.1.3.6.1.4.1.674.10903.200.2.200.150.2.*')
    ),
    parse_function=parse_dell_rackpdu_sensor_temp,
    fetch=[
        SNMPTree(
            base='.1.3.6.1.4.1.674.10903.200.2.200.150.2.3.1',
            oids=[
                '2',  # DellrPDU-MIB::rPDUSensorTempConfigName
                '7',  # DellrPDU-MIB::rPDUSnsorTempCfgTempHighThreshC
                '6',  # DellrPDU-MIB::rPDUSensorTempCfgTempMaxThreshC
            ]),
        SNMPTree(
            base='.1.3.6.1.4.1.674.10903.200.2.200.150.2.2.1',
            oids=[
                '2',  # DellrPDU-MIB::rPDUSensorTempStatusName
                '5',  # DellrPDU-MIB::rPDUSensorTempStatusTempC
                '6',  # DellrPDU-MIB::rPDUSensorTempStatusAlarmStatus
            ]),
    ],
)


def discovery_dell_rackpdu_sensor_temp(section):
    for sensor in section.keys():
        if section[sensor][1] == 1:
            continue
        yield Service(item=sensor)


def check_dell_rackpdu_sensor_temp(item, params, section):
    if item not in section:
        return

    temperature, status, warn, crit = section[item]

    yield from check_temperature(
        reading=temperature,
        params=params,
        unique_name='heck_dell_rackpdu_sensor_temp.%s' % item,
        dev_levels=(warn, crit),
        dev_status=DELL_RACKPDU_SENSOR_LEVEL_STATES[status],
        dev_status_name=item,
    )


register.check_plugin(
    name='dell_rackpdu_sensor_temp',
    service_name='%s Temperature',
    discovery_function=discovery_dell_rackpdu_sensor_temp,
    check_function=check_dell_rackpdu_sensor_temp,
    check_default_parameters={},
    check_ruleset_name='temperature',
)
