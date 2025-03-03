import asyncio
import contextlib
import enum
import logging
import signal
from unittest.mock import patch

from sdbus.utils import (
    parse,
    parse_interfaces_added as sdbus_parse_interfaces_added,
    parse_interfaces_removed as sdbus_parse_interfaces_removed,
    parse_get_managed_objects as sdbus_parse_get_managed_objects,
)

from onetouchcopy.udisks2_interfaces import Filesystem, Block, PartitionBlock

FILESYSTEM_IFACE = "org.freedesktop.UDisks2.Filesystem"
PARTITION_TABLE_IFACE = "org.freedesktop.UDisks2.PartitionTable"
BLOCK_IFACE = "org.freedesktop.UDisks2.Block"
INTERFACES = (Filesystem, Block, PartitionBlock)


class Led:
    def __init__(self, name: str, logger: logging.Logger):
        self._name = name
        self._logger = logger

    def on(self):
        self._write("trigger", "none")
        self._write("brightness", "1")

    def off(self):
        self._write("trigger", "none")
        self._write("brightness", "0")

    @contextlib.contextmanager
    def blink(self):
        self._write("trigger", "timer")
        self._write("brightness", "1")
        self._write("delay_on", "200")
        self._write("delay_off", "200")
        yield
        self.on()

    def _write(self, filename: str, content: str):
        file = f"/sys/class/leds/qnap8528::{self._name}/{filename}"
        try:
            with open(file, "w") as f:
                f.write(content)
                self._logger.debug(f"Written {content} to {file}")
        except OSError:
            self._logger.debug(f"Can't write to {file}")


class LogLevels(enum.IntEnum):
    SERVICE_LIFECYCLE = logging.INFO + 5


def _get_class_from_interfaces(_1, interface_names_iter, _2):
    if PARTITION_TABLE_IFACE in interface_names_iter:
        return PartitionBlock
    if FILESYSTEM_IFACE in interface_names_iter:
        return Filesystem
    elif BLOCK_IFACE in interface_names_iter:
        return Block
    return None


def parse_interfaces_added(path, interfaces_added_data):
    with patch(f"{parse.__name__}._get_class_from_interfaces") as f:
        f.side_effect = _get_class_from_interfaces
        return sdbus_parse_interfaces_added(
            INTERFACES, (path, interfaces_added_data), "none", "ignore"
        )


def parse_interfaces_removed(path, interfaces_removed_data):
    with patch(f"{parse.__name__}._get_class_from_interfaces") as f:
        f.side_effect = _get_class_from_interfaces
        return sdbus_parse_interfaces_removed(INTERFACES, (path, interfaces_removed_data), "none")


def parse_get_managed_objects(managed_objects_data):
    with patch(f"{parse.__name__}._get_class_from_interfaces") as f:
        f.side_effect = _get_class_from_interfaces
        return sdbus_parse_get_managed_objects(INTERFACES, managed_objects_data, "none", "ignore")


async def await_sig():
    def handler(signum):
        if not future.done():
            future.set_result(signum)

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, handler, signal.SIGINT)
    loop.add_signal_handler(signal.SIGTERM, handler, signal.SIGTERM)
    loop.add_signal_handler(signal.SIGHUP, handler, signal.SIGTERM)
    await future
