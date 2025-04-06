import argparse
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Any, Optional

import can
from can import CanutilsLogReader
from can.notifier import MessageRecipient
from construct.lib import Container

import can_messages

logger = logging.getLogger("can.reader")


@dataclass
class BatteryStatus:
    soc: int | None
    voltage: float | None
    current: float | None
    temperature: float | None


_battery_status = BatteryStatus(None, None, None, None)
_battery_status_update = asyncio.Event()


def _container_to_dict(container: dict | Container):
    if isinstance(container, Container):
        return {k: _container_to_dict(v) for k, v in container.items() if k != "_io"}
    else:
        return container


def _process_message(msg: can.Message) -> Optional[Any]:
    parsed = can_messages.parse_message(msg)
    logger.debug(
        "Parsed Message 0x%x: %s", msg.arbitration_id, _container_to_dict(parsed)
    )
    if msg.arbitration_id == 0x356:
        _battery_status.voltage = parsed.voltage
        _battery_status.current = parsed.current
        _battery_status.temperature = parsed.avg_cell_temperature
        _battery_status_update.set()
    elif msg.arbitration_id == 0x355:
        _battery_status.soc = parsed.state_of_charge
        _battery_status_update.set()

    return parsed


async def read_dump(file):
    unknown_messages = set()
    log_reader = CanutilsLogReader(file)
    for msg in log_reader:
        parsed = _process_message(msg)
        logger.debug(
            "Parsed Message 0x%x: %s", msg.arbitration_id, _container_to_dict(parsed)
        )
        if parsed is None:
            unknown_messages.add(msg.arbitration_id)

    if unknown_messages:
        logger.warning("Unknown message id: %s", [hex(i) for i in unknown_messages])


async def status_reporter():
    try:
        while True:
            await _battery_status_update.wait()
            await asyncio.sleep(0.100)
            if (
                _battery_status.soc is not None
                and _battery_status.voltage is not None
                and _battery_status.current is not None
                and _battery_status.temperature is not None
            ):
                logger.info(
                    "Battery Status: %d%% %.2fV %0.2fA %0.0fC°",
                    _battery_status.soc,
                    _battery_status.voltage,
                    _battery_status.current,
                    _battery_status.temperature,
                )
            _battery_status_update.clear()
    except asyncio.CancelledError:
        pass
    except:
        logger.exception("Unexpected error")


async def amain(interface, candump_log):
    if candump_log:
        await read_dump(candump_log)
        return

    status_reporter_task = asyncio.create_task(status_reporter())
    try:
        with can.Bus(interface="socketcan", channel=interface, bitrate=500000) as bus:
            reader = can.AsyncBufferedReader()
            listeners: List[MessageRecipient] = [reader]
            loop = asyncio.get_running_loop()
            notifier = can.Notifier(bus, listeners, loop=loop)
            try:
                async for msg in reader:
                    _process_message(msg)
            finally:
                notifier.stop()
    except asyncio.CancelledError:
        pass
    finally:
        status_reporter_task.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="can-reader")
    parser.add_argument("--interface", "-i", default="can0")
    parser.add_argument("--candump-log", "-l")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    args = parser.parse_args()

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    if args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig()

    asyncio.run(amain(args.interface, args.candump_log))
