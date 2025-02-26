import asyncio
import logging
import sys
from asyncio import Task
from logging import getLogger
from pathlib import Path
from typing import Any

from evdev import list_devices as list_evdev, ecodes, InputDevice
from sdbus import DbusObjectManagerInterfaceAsync, sd_bus_open_system

from src.udisks2_interfaces import Filesystem

KERNEL_MODULE_NAME = "qnap8528"
DEST = "/home/yunohost.multimedia/share/Dump"
WELL_KNOWN_DEV = "/dev/qnap-one-touch-copy"

DRIVE_IFACE = "org.freedesktop.UDisks2.Drive"
FILESYSTEM_IFACE = "org.freedesktop.UDisks2.Filesystem"
BLOCK_IFACE = "org.freedesktop.UDisks2.Block"


logger = getLogger("YNH one touch copy")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class Udisks2Manager:
    @property
    async def filesystems(self) -> list[Filesystem] | None:
        async with self._lock:
            return (
                None
                if not self._found_drive
                else [
                    Filesystem.new_proxy("org.freedesktop.UDisks2", it, self._bus)
                    for it in self._found_drive["Partitions"]
                ]
            )

    def __init__(self):
        self._bus = sd_bus_open_system()
        self._object_manager = DbusObjectManagerInterfaceAsync.new_proxy(
            "org.freedesktop.UDisks2", "/org/freedesktop/UDisks2", self._bus
        )

        self._lock = asyncio.Lock()
        self._tasks: list[Task] = []

        self._filesystems: dict[str, dict[str, Any]] = {}
        self._found_drive = None

    async def _listen_interfaces_added(self):
        async for object_path, interfaces_and_properties in self._object_manager.interfaces_added:
            async with self._lock:
                self._populate_known_objects(object_path, interfaces_and_properties)

    async def _listen_interfaces_removed(self):
        async for object_path, interfaces_and_properties in self._object_manager.interfaces_removed:
            async with self._lock:
                if BLOCK_IFACE not in interfaces_and_properties:
                    return

                dev_path = (
                    interfaces_and_properties[BLOCK_IFACE]["Device"].decode().removesuffix("\x00")
                )
                if self._match_disk(interfaces_and_properties):
                    self._found_drive = None
                    self._filesystems.clear()
                    logger.info(f"Matching device {dev_path} was removed; clearing…")
                elif FILESYSTEM_IFACE in interfaces_and_properties:
                    self._filesystems.pop(object_path, None)
                    logger.info(f"Removed filesystem {dev_path}")

    async def _get_managed_objects(self):
        async with self._lock:
            objects = await self._object_manager.get_managed_objects()
            for object_path, interfaces_and_properties in objects.items():
                self._populate_known_objects(object_path, interfaces_and_properties)

    def _populate_known_objects(
        self, object_path: str, interfaces_and_properties: dict[str, dict[str, tuple[str, Any]]]
    ):
        if BLOCK_IFACE not in interfaces_and_properties:
            return

        found_drive = self._match_disk(interfaces_and_properties)

        if not found_drive and FILESYSTEM_IFACE not in interfaces_and_properties:
            return

        props: dict[str, Any] = {}
        for iface_name, iface_dict in interfaces_and_properties.items():
            props.setdefault("_interfaces", set())
            props["_interfaces"].add(iface_name)
            props["_object_path"] = object_path
            props.update({k: v for k, (_, v) in iface_dict.items()})

        dev_path = props["Device"].decode().removesuffix("\x00")
        if found_drive:
            if not props.get("Partitions", None):
                logger.info(
                    f"Found matching drive {dev_path} but it's not partitionned; nothing will be copied"
                )
                return
            self._found_drive = props
            logger.info(f"Found matching drive {dev_path}")
        else:
            self._filesystems[object_path] = props
            logger.info(f"Found filesystem {dev_path}")

    def _match_disk(self, interfaces_and_properties: dict[str, dict[str, tuple[str, Any]]]):
        symlinks = {
            it.decode().removesuffix("\x00")
            for it in interfaces_and_properties.get(BLOCK_IFACE, {}).get("Symlinks", (None, []))[1]
        }

        return WELL_KNOWN_DEV in symlinks

    async def start(self):
        await self._get_managed_objects()
        loop = asyncio.get_event_loop()
        self._tasks.append(loop.create_task(self._listen_interfaces_added()))
        self._tasks.append(loop.create_task(self._listen_interfaces_removed()))

    async def stop(self):
        self._found_drive = None
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks)


class Service:
    def __init__(self, device: InputDevice, manager: Udisks2Manager):
        self._device = device
        self._manager = manager

        self._lock = asyncio.Lock()
        self._ongoing_process = None
        self._listen_task = None

    async def _read_stream(self, stream):
        while line := await stream.readline():
            logger.info(line)

    async def _copy(self, src):
        return await asyncio.sleep(120)
        # self.ongoing_process = await asyncio.create_subprocess_exec(
        #     "rsync",
        #     "--progress",
        #     "--compress",
        #     "--recursive",
        #     "--update",
        #     src,
        #     DEST,
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE,
        # )
        #
        # await asyncio.gather(self._read_stream(self.ongoing_process.stdout), self._read_stream(self.ongoing_process.stderr))
        # return await self.ongoing_process.wait()

    def _copy_done(self, task: Task):
        if task.cancelled():
            logger.info("Copy cancelled")
        elif e := task.exception():
            logger.warning("An error happened during the copy", exc_info=e)
        else:
            logger.info("Copy done")
        self._ongoing_process = None

    async def _listen_button_evts(self):
        async for event in self._device.async_read_loop():
            if event.type != ecodes.EV_KEY or event.code != ecodes.BTN_2:
                continue

            async with self._lock:
                if self._ongoing_process is not None:
                    logger.info("Copy process already encours")
                    continue

                filesystems = await self._manager.filesystems
                if not filesystems:
                    logger.info("No filesystem found")
                    continue

                for filesystems in filesystems:
                    mnt_pnt = await filesystems.mount_point
                    if not mnt_pnt:
                        mnt_pnt = await filesystems.mount({"auth.no_user_interaction": ("b", True)})
                    if not mnt_pnt:
                        logger.error(f"Couldn't mount filesystem located at {filesystems.device}")
                        continue

                logger.info("Starting copy")

                self._ongoing_process = asyncio.get_event_loop().create_task(self._copy(mnt_pnt))
                self._ongoing_process.add_done_callback(self._copy_done)

    async def start(self):
        loop = asyncio.get_event_loop()
        self._listen_task = loop.create_task(self._listen_button_evts())

    async def stop(self):
        tasks = []
        if self._listen_task:
            self._listen_task.cancel()
            tasks.append(self._listen_task)

        if self._ongoing_process:
            self._ongoing_process.cancel()
            tasks.append(self._ongoing_process)

        await asyncio.gather(*tasks)


async def main() -> int:
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

    manager = Udisks2Manager()
    await manager.start()
    service = Service(device, manager)
    await service.start()

    return 0


if __name__ == "__main__":
    _loop = asyncio.get_event_loop()
    _loop.run_until_complete(main())
    _loop.run_forever()
    raise SystemExit(main())
