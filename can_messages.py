import logging
from enum import IntEnum
from typing import Any, Optional

import can
from construct import (
    Struct,
    Const,
    BitStruct,
    Flag,
    Padding,
    Byte,
    Int16sl,
    ExprAdapter,
    obj_,
    Int16ul,
    PaddedString,
    Int8ul,
    BitsInteger,
    ByteSwapped,
)

can_359_alarms_and_warnings = Struct(
    "protection"
    / BitStruct(
        # Byte 0
        "discharge_over_current" / Flag,
        Flag,
        Flag,
        "cell_under_temperature" / Flag,
        "cell_over_temperature" / Flag,
        "cell_or_module_under_voltage" / Flag,
        "cell_or_module_over_voltage" / Flag,
        Flag,
        # Byte 1
        Flag,
        Flag,
        Flag,
        Flag,
        "system_error" / Flag,
        Flag,
        Flag,
        "charge_over_current" / Flag,
    ),
    "alarm"
    / BitStruct(
        # Byte 2
        "discharge_high_current" / Flag,
        Flag,
        Flag,
        "cell_low_temperature" / Flag,
        "cell_high_temperature" / Flag,
        "cell_or_module low voltage" / Flag,
        "cell_or_module_high_voltage" / Flag,
        Flag,
        # Byte 3
        Flag,
        Flag,
        Flag,
        Flag,
        "internal_communication_fail" / Flag,
        Flag,
        Flag,
        "charge_high_current" / Flag,
    ),
    "model_numbers" / Int8ul,
    "P" / Byte,
    "N" / Byte,
)

BatteryVoltage = ExprAdapter(Int16sl, obj_ * 0.01, obj_ / 0.01)
BatteryAmpere = ExprAdapter(Int16sl, obj_ * 0.1, obj_ / 0.1)
BatteryCelicius = ExprAdapter(Int16sl, obj_ * 0.1, obj_ / 0.1)

can_351_bms_instructions = Struct(
    "battery_charge_voltage" / ExprAdapter(Int16sl, obj_ * 0.1, obj_ / 0.1),
    "charge_current_limit" / BatteryAmpere,
    "discharge_current_limit" / BatteryAmpere,
)

can_355_state = Struct(
    "state_of_charge" / Int16ul,
    "state_of_health" / Int16ul,
)

can_356 = Struct(
    "voltage" / BatteryVoltage,
    "current" / BatteryAmpere,
    "avg_cell_temperature" / BatteryCelicius,
)

can_35C = Struct(
    "request_flag"
    / BitStruct(
        "charge_enable" / Flag,
        "discharge_enable" / Flag,
        "request_force_charge_1" / Flag,
        "request_force_charge_2" / Flag,
        "request_full_charge" / Flag,
        Flag,
        Flag,
        Flag,
    ),
    Padding(1),
)

can_35E = Struct("manufacturer_name" / PaddedString(2, encoding="ascii"))

can_305 = Struct("inverter_reply" / Padding(8))

can_307_victron = Struct(
    Const(0x12, Byte),
    Const(0x34, Byte),
    Const(0x56, Byte),
    Const(0x78, Byte),
    Const(ord("V"), Byte),
    Const(ord("I"), Byte),
    Const(ord("C"), Byte),
    Const(0x00, Byte),
)

can_372_bank_info = Struct(
    "modules_online" / Int16ul,
    "modules_blocking_charge" / Int16ul,
    "modules_blocking_discharge" / Int16ul,
    "modules_offline" / Int16ul,
)

KelvinToCelsius = ExprAdapter(Int16ul, obj_ - 273.15, obj_ + 273.15)
CellVoltage = ExprAdapter(Int16ul, obj_ * 0.001, obj_ / 0.001)
can_373_cell_info = Struct(
    "min_cell_voltage" / CellVoltage,
    "max_cell_voltage" / CellVoltage,
    "min_cell_temperature" / KelvinToCelsius,
    "max_cell_temperature" / KelvinToCelsius,
)

can_374_min_cell_voltage_id = Struct("cell_id" / PaddedString(8, encoding="ascii"))

can_375_max_cell_voltage_id = Struct("cell_id" / PaddedString(8, encoding="ascii"))

can_376_min_cell_temperature_id = Struct("cell_id" / PaddedString(8, encoding="ascii"))

can_377_max_cell_temperature_id = Struct("cell_id" / PaddedString(8, encoding="ascii"))

can_379 = Struct("installed_capacity_ah" / Int16ul, Padding(2))


class VictronFlagValue(IntEnum):
    UNSUPPORTED = 0
    INACTIVE = 1
    ACTIVE = 2

    def to_bool(self) -> Optional[bool]:
        if self == self.UNSUPPORTED:
            return None

        return self == self.ACTIVE

    @classmethod
    def from_bool(cls, value: Optional[bool]) -> "VictronFlagValue":
        if value is None:
            return cls.UNSUPPORTED

        return cls.ACTIVE if value == True else cls.INACTIVE


VictronFlag = ExprAdapter(
    ByteSwapped(BitsInteger(2)),
    lambda obj, context: VictronFlagValue(obj).to_bool(),
    lambda obj, context: VictronFlagValue.from_bool(obj).value,
)


can_35A_alarms_and_warnings_victron = Struct(
    "alarm"
    / BitStruct(
        "general_alarm" / VictronFlag,
        "battery_high_voltage" / VictronFlag,
        "battery_low_voltage" / VictronFlag,
        "battery_high_temperature" / VictronFlag,
        "battery_low_temperature" / VictronFlag,
        "battery_high_temperature_charge" / VictronFlag,
        "battery_low_temperature_charge" / VictronFlag,
        "battery_high_current" / VictronFlag,
        "battery_high_charge_current" / VictronFlag,
        "contactor" / VictronFlag,
        "short_circuit" / VictronFlag,
        "bms_internal" / VictronFlag,
        "cell_imbalance" / VictronFlag,
        BitsInteger(2),
        BitsInteger(2),
        BitsInteger(2),
    ),
    "warning"
    / BitStruct(
        "general_warning" / VictronFlag,
        "battery_high_voltage" / VictronFlag,
        "battery_low_voltage" / VictronFlag,
        "battery_high_temperature" / VictronFlag,
        "battery_low_temperature" / VictronFlag,
        "battery_high_temperature_charge" / VictronFlag,
        "battery_low_temperature_charge" / VictronFlag,
        "battery_high_current" / VictronFlag,
        "battery_high_charge_current" / VictronFlag,
        "contactor" / VictronFlag,
        "short_circuit" / VictronFlag,
        "bms_internal" / VictronFlag,
        "cell_imbalance" / VictronFlag,
        BitsInteger(2),
        BitsInteger(2),
        BitsInteger(2),
    ),
)


def parse_message(msg: can.Message) -> Optional[Any]:
    if msg.arbitration_id == 0x305:
        parsed = can_305.parse(msg.data)
    elif msg.arbitration_id == 0x307:
        parsed = can_307_victron.parse(msg.data)
    elif msg.arbitration_id == 0x359:
        parsed = can_359_alarms_and_warnings.parse(msg.data)
    elif msg.arbitration_id == 0x351:
        parsed = can_351_bms_instructions.parse(msg.data)
    elif msg.arbitration_id == 0x355:
        parsed = can_355_state.parse(msg.data)
    elif msg.arbitration_id == 0x356:
        parsed = can_356.parse(msg.data)
    elif msg.arbitration_id == 0x35A:
        parsed = can_35A_alarms_and_warnings_victron.parse(msg.data)
    elif msg.arbitration_id == 0x35C:
        parsed = can_35C.parse(msg.data)
    elif msg.arbitration_id == 0x35E:
        parsed = can_35E.parse(msg.data)
    elif msg.arbitration_id == 0x372:
        parsed = can_372_bank_info.parse(msg.data)
    elif msg.arbitration_id == 0x373:
        parsed = can_373_cell_info.parse(msg.data)
    elif msg.arbitration_id == 0x374:
        parsed = can_374_min_cell_voltage_id.parse(msg.data)
    elif msg.arbitration_id == 0x375:
        parsed = can_375_max_cell_voltage_id.parse(msg.data)
    elif msg.arbitration_id == 0x376:
        parsed = can_376_min_cell_temperature_id.parse(msg.data)
    elif msg.arbitration_id == 0x377:
        parsed = can_377_max_cell_temperature_id.parse(msg.data)
    elif msg.arbitration_id == 0x379:
        parsed = can_379.parse(msg.data)
    else:
        logging.debug("Unknown message: %x %s", msg.arbitration_id, msg.data)
        return None
    return parsed
