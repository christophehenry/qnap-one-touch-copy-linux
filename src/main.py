import asyncio
import logging
import os.path
import sys
from contextlib import AbstractAsyncContextManager
from logging import getLogger
from pathlib import Path
from typing import Any, Coroutine

from evdev import list_devices as list_evdev, ecodes, InputDevice
from sdbus import DbusObjectManagerInterfaceAsync, sd_bus_open_system
from sdbus.dbus_proxy_async_interface_base import DbusInterfaceBaseAsync

from src.udisks2_interfaces import Filesystem, Block, PartitionBlock
from src.utils import (
    parse_get_managed_objects,
    await_sig,
    parse_interfaces_added,
    parse_interfaces_removed,
)

KERNEL_MODULE_NAME = "qnap8528"
DEST = "/home/yunohost.multimedia/share/Dump"
WELL_KNOWN_DEV = "/dev/qnap-one-touch-copy"

DRIVE_IFACE = "org.freedesktop.UDisks2.Drive"
FILESYSTEM_IFACE = "org.freedesktop.UDisks2.Filesystem"
BLOCK_IFACE = "org.freedesktop.UDisks2.Block"


logger = getLogger("YNH one touch copy")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class Udisks2Manager(AbstractAsyncContextManager):
    @property
    async def filesystems(self) -> list[Filesystem] | None:
        async with self._lock:
            return (
                None
                if not self._found_drive
                else [
                    Filesystem.new_proxy("org.freedesktop.UDisks2", it, self._bus)
                    for it in self._found_drive["partitions"]
                ]
            )

    @property
    def _found_drive(self):
        return self._m_found_drive

    @_found_drive.setter
    def _found_drive(self, value):
        self._m_found_drive = value
        if not value:
            self._filesystems.clear()

    def __init__(self):
        self._bus = sd_bus_open_system()
        self._object_manager = DbusObjectManagerInterfaceAsync.new_proxy(
            "org.freedesktop.UDisks2", "/org/freedesktop/UDisks2", self._bus
        )

        self._lock = asyncio.Lock()
        self._tasks: set[asyncio.Task] = set()

        self._filesystems: dict[str, dict[str, Any]] = {}
        self._m_found_drive: dict[str, Any] | None = None

    async def _listen_interfaces_added(self):
        async for object_path, interfaces_and_properties in self._object_manager.interfaces_added:
            async with self._lock:
                _, iface, properties = parse_interfaces_added(interfaces_and_properties)
                if iface is not None:
                    self._populate_known_objects(object_path, iface, properties)

    async def _listen_interfaces_removed(self):
        async for object_path, interfaces_and_properties in self._object_manager.interfaces_removed:
            async with self._lock:
                _, iface = parse_interfaces_removed(interfaces_and_properties)

                if not issubclass(iface, Block):
                    return

                if self._found_drive["_object_path"] == object_path:
                    self._found_drive = None
                else:
                    self._filesystems.pop(object_path, None)

    async def _get_managed_objects(self):
        async with self._lock:
            objs = parse_get_managed_objects(await self._object_manager.get_managed_objects())
            for object_path, (iface, props) in objs.items():
                if iface is not None:
                    self._populate_known_objects(object_path, iface, props)

    def _populate_known_objects(
        self, object_path: str, iface: DbusInterfaceBaseAsync, properties: dict[str, Any]
    ):
        found_drive = self._match_disk(properties)

        if not found_drive and iface is not Filesystem:
            return

        dev_path = properties["device"].decode().removesuffix("\x00")
        properties["_object_path"] = object_path
        if found_drive:
            if iface is not PartitionBlock:
                logger.info(
                    f"Found matching drive {dev_path} but it's not partitionned; "
                    f"nothing will be copied"
                )
                return
            self._found_drive = properties
            logger.info(f"Found matching drive {dev_path}")
        else:
            self._filesystems[object_path] = properties
            logger.info(f"Found filesystem {dev_path}")

    def _match_disk(self, properties: dict[str, Any]):
        symlinks = {it.decode().removesuffix("\x00") for it in properties.get("symlinks", [])}
        return WELL_KNOWN_DEV in symlinks

    async def _create_tasks(self, *coros: Coroutine):
        def done_callback(task: asyncio.Task):
            self._tasks.discard(task)
            if task.cancelled():
                logger.debug("Stopped listening udisk event")
            elif e := task.exception():
                logger.error(e)

        loop = asyncio.get_event_loop()
        for coro in coros:
            t = loop.create_task(coro)
            t.add_done_callback(done_callback)
            self._tasks.add(t)

    async def __aenter__(self):
        await self._get_managed_objects()
        await self._create_tasks(self._listen_interfaces_added(), self._listen_interfaces_removed())
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        logger.debug("Stopping listening to udisks events…")
        self._found_drive = None
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.debug("Stopped listening to udisks events")


class Service(AbstractAsyncContextManager):
    def __init__(self, device: InputDevice, manager: Udisks2Manager):
        self._device = device
        self._manager = manager

        self._lock = asyncio.Lock()
        self._tasks: set[asyncio.Task] = set()
        self._listen_task: asyncio.Task | None = None

    async def _read_stream(self, stream):
        while line := await stream.readline():
            logger.info(line)

    async def _copy(self, src, dest):
        return await asyncio.sleep(120)
        # self.ongoing_process = await asyncio.create_subprocess_exec(
        #     "rsync",
        #     "--progress",
        #     "--compress",
        #     "--recursive",
        #     "--update",
        #     src,
        #     dest,
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE,
        # )
        #
        # await asyncio.gather(self._read_stream(self.ongoing_process.stdout), self._read_stream(self.ongoing_process.stderr))
        # return await self.ongoing_process.wait()

    async def _create_copy_tasks(self, *sources: str):
        def done_callback(task: asyncio.Task):
            self._tasks.discard(task)
            if task.cancelled():
                logger.info("Copy cancelled")
            elif e := task.exception():
                logger.warning("An error happened during the copy", exc_info=e)
            else:
                logger.info("Copy done")

        loop = asyncio.get_event_loop()
        async with self._lock:
            for source in sources:
                dest = Path(DEST) / os.path.basename(source)
                try:
                    dest.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.error(f"Unable to create destination directory {dest}", exc_info=e)
                    continue

                logger.info(f"Starting copy of {source} to {dest}")
                t = loop.create_task(self._copy(source, dest))
                t.set_name(f"copy task from {source} to {dest}")
                t.add_done_callback(done_callback)
                self._tasks.add(t)

    async def _listen_button_evts(self):
        async for event in self._device.async_read_loop():
            if event.type != ecodes.EV_KEY or event.code != ecodes.BTN_2:
                continue

            async with self._lock:
                if len(self._tasks):
                    logger.info("Copy process already encours")
                    continue

                filesystems = await self._manager.filesystems
                if not filesystems:
                    logger.info("No filesystem found")
                    continue

                mnt_pnts = set()

                for filesystems in filesystems:
                    mnt_pnt = await filesystems.mount_point
                    if not mnt_pnt:
                        mnt_pnt = await filesystems.mount({"auth.no_user_interaction": ("b", True)})
                    if not mnt_pnt:
                        logger.error(f"Couldn't mount filesystem located at {filesystems.device}")
                        continue
                    mnt_pnts.add(mnt_pnt)
                await self._create_copy_tasks(*mnt_pnts)

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        self._listen_task = loop.create_task(self._listen_button_evts())
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        tasks = []
        if self._listen_task:
            self._listen_task.cancel()
            tasks.append(self._listen_task)

        async with self._lock:
            for copy_task in self._tasks:
                tasks.append(copy_task)
                logger.info(f"Stopping {copy_task.get_name()}")

            await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    try:
        device = next(
            device
            for path in list_evdev()
            if (device := InputDevice(path)).name == KERNEL_MODULE_NAME
        )
    except StopIteration:
        logger.error(f"Firmware {KERNEL_MODULE_NAME} couldn't be found on the device")
        return 1

    path = Path(DEST)
    path.mkdir(0o777, exist_ok=True)

    logger.info("Service started")

    async with Udisks2Manager() as manager, Service(device, manager):
        await await_sig()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.get_event_loop().run_until_complete(main()))
