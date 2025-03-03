import asyncio
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


def parse_interfaces_added(interfaces_added_data):
    with patch(f"{parse.__name__}._get_class_from_interfaces") as f:
        f.side_effect = _get_class_from_interfaces
        return sdbus_parse_interfaces_added(INTERFACES, interfaces_added_data, "none", "ignore")


def parse_interfaces_removed(interfaces_removed_data):
    with patch(f"{parse.__name__}._get_class_from_interfaces") as f:
        f.side_effect = _get_class_from_interfaces
        return sdbus_parse_interfaces_removed(INTERFACES, interfaces_removed_data, "none")


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
    await future
