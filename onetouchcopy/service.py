import asyncio
import logging
import re
import shlex
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Any

from evdev import ecodes, InputDevice, KeyEvent
from sdbus import DbusObjectManagerInterfaceAsync, sd_bus_open_system
from sdbus.dbus_proxy_async_interface_base import DbusInterfaceBaseAsync

from onetouchcopy.udisks2_interfaces import Filesystem, Block, PartitionBlock, DeviceBusyError
from onetouchcopy.utils import (
    parse_get_managed_objects,
    parse_interfaces_added,
    parse_interfaces_removed,
    LogLevels,
    Led,
)

WELL_KNOWN_DEV = "/dev/qnap-one-touch-copy"

DRIVE_IFACE = "org.freedesktop.UDisks2.Drive"
FILESYSTEM_IFACE = "org.freedesktop.UDisks2.Filesystem"
BLOCK_IFACE = "org.freedesktop.UDisks2.Block"


logger = logging.getLogger("One touch copy daemon")


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
        return self._found_drive_value

    @_found_drive.setter
    def _found_drive(self, value):
        self._found_drive_value = value
        if value:
            self._led.on()
        else:
            self._led.off()
            self._filesystems.clear()

    def __init__(self):
        super().__init__()
        self._bus = sd_bus_open_system()
        self._object_manager = DbusObjectManagerInterfaceAsync.new_proxy(
            "org.freedesktop.UDisks2", "/org/freedesktop/UDisks2", self._bus
        )

        self._lock = asyncio.Lock()
        self._tasks: set[asyncio.Task] = set()

        self._filesystems: dict[str, dict[str, Any]] = {}
        self._found_drive_value: dict[str, Any] | None = None

        self._led = Led("usb", logger)

    async def _listen_interfaces_added(self):
        async for object_path, interfaces_and_properties in self._object_manager.interfaces_added:
            async with self._lock:
                _, iface, properties = parse_interfaces_added(
                    object_path, interfaces_and_properties
                )
                if iface is not None:
                    self._populate_known_objects(object_path, iface, properties)

    async def _listen_interfaces_removed(self):
        async for object_path, interfaces_and_properties in self._object_manager.interfaces_removed:
            async with self._lock:
                _, iface = parse_interfaces_removed(object_path, interfaces_and_properties)

                if not iface or not issubclass(iface, Block):
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
                logger.warning(
                    f"Found matching drive {dev_path} but it's not partitionned; "
                    f"nothing will be copied"
                )
                return
            self._found_drive = properties
            logger.info(f"Found matching drive {dev_path}")
        else:
            self._filesystems[object_path] = properties
            logger.debug(f"Found filesystem {dev_path}")

    def _match_disk(self, properties: dict[str, Any]):
        symlinks = {it.decode().removesuffix("\x00") for it in properties.get("symlinks", [])}
        return WELL_KNOWN_DEV in symlinks

    def _done_callback(self, task: asyncio.Task):
        self._tasks.discard(task)
        if task.cancelled():
            logger.debug(f"Stopped listening udisk's {task.get_name()} event")
        elif e := task.exception():
            logger.error(e)

    async def __aenter__(self):
        self._led.off()
        await self._get_managed_objects()
        for name, coro in {
            "interfaces added": self._listen_interfaces_added(),
            "interfaces removed": self._listen_interfaces_removed(),
        }.items():
            t = asyncio.get_event_loop().create_task(coro, name=name)
            t.add_done_callback(self._done_callback)
            self._tasks.add(t)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        self._found_drive = None
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        return await super().__aexit__(exc_type, exc_value, traceback)


class FilesystemUnmountableError(Exception):
    def __init__(self, device: str):
        super().__init__(f"Couldn't mount filesystem located at {device}")
        self.device = device


class CopyDestUnwritableError(Exception):
    def __init__(self, dest: str):
        super().__init__(f"Unable to create destination directory {dest}")
        self.dest = dest


class CopyTask:
    @property
    def _log_message(self):
        return f"{' of %s' % self.src if self.src else ''} to {self.dest}"

    def __init__(self, filesystem: Filesystem, dest: str):
        self.src = None
        self.dest = dest

        self._filesystem = filesystem
        self._progress_value = 0
        self._already_mounted = False
        self._percent_regex = re.compile(r"(?P<progress>\d+)%")
        self._trailing_slash_regex = re.compile(r"/*$")
        self._task: None | asyncio.Task = None

    async def _mount(self) -> str:
        # Step 1: try mount endpoint
        mount_point = await self._filesystem.mount_point
        if mount_point:
            self._already_mounted = True
        else:
            mount_point = await self._filesystem.mount({"auth.no_user_interaction": ("b", True)})
            if not mount_point:
                raise FilesystemUnmountableError(await self._filesystem.device)

        return mount_point

    def _parse_line(self, line: str):
        match = self._percent_regex.search(line)
        if not match:
            return
        value = int(match.group("progress"))
        if value > self._progress_value:
            self._progress_value = value
            logger.info(f"Copy progress: {value}%")

    async def _process_stdout(self, process):
        try:
            while line := await process.stdout.readuntil(b"\r"):
                self._parse_line(line.decode())
        except asyncio.IncompleteReadError as e:
            self._parse_line(e.partial.decode())

    async def _copy_process(self, src: str, dest: str):
        # Removing trailing slashed will create the additionnal directory on dest
        src = self._trailing_slash_regex.sub("", src)
        dest = self._trailing_slash_regex.sub("", dest)
        async with asyncio.TaskGroup() as group:
            args = shlex.join(
                ["--compress", "--recursive", "--update", "--info=progress2", src, dest]
            )
            logger.debug(f"Running 'rsync {args}")
            copy_task = await asyncio.create_subprocess_exec(
                "rsync",
                *shlex.split(args),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            group.create_task(copy_task.wait())
            group.create_task(self._process_stdout(copy_task))

    async def run(self) -> Exception | None:
        try:
            self.src = self._trailing_slash_regex.sub("", await self._mount())
            logger.log(LogLevels.SERVICE_LIFECYCLE, f"Starting copy{self._log_message}")
            await self._copy_process(self.src, self.dest)
        except asyncio.CancelledError:
            logger.info(f"Copy{self._log_message} cancelled")
        except (CopyDestUnwritableError, FilesystemUnmountableError) as e:
            logger.error(f"{e}")
        except Exception as e:
            logger.error(f"An unexpected error happened during copy{self._log_message}", exc_info=e)
        finally:
            if not self._already_mounted:
                dev = await self._filesystem.device
                try:
                    await self._filesystem.unmount({"auth.no_user_interaction": ("b", True)})
                    logger.log(LogLevels.SERVICE_LIFECYCLE, f"Unmounted {dev}")
                except DeviceBusyError:
                    logger.warning(f"Can't auto-unmount {dev}: device is busy")


class Service(AbstractAsyncContextManager):
    def __init__(self, device: InputDevice, manager: Udisks2Manager, dest: Path):
        self._device = device
        self._manager = manager
        self._dest = dest.resolve()

        self._copy_task: asyncio.Task | None = None
        self._listen_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

        self._led = Led("usb", logger)

    def _copy_task_done(self, _):
        self._copy_task = None

    async def _run_copy(self):
        filesystems = await self._manager.filesystems
        if not filesystems:
            logger.info("No filesystem found")
            return

        with self._led.blink():
            async with asyncio.TaskGroup() as group:
                for filesystem in filesystems:
                    group.create_task(CopyTask(filesystem, f"{self._dest}").run())

    async def _listen_button_evts(self):
        async for event in self._device.async_read_loop():
            if (
                event.type != ecodes.EV_KEY
                or event.code != ecodes.BTN_2
                or event.value != KeyEvent.key_up
            ):
                continue

            async with self._lock:
                if self._copy_task:
                    logger.warning("Copy process already encours; ignoring input…")
                    continue

                self._copy_task = asyncio.get_event_loop().create_task(self._run_copy())
                self._copy_task.add_done_callback(self._copy_task_done)

    async def __aenter__(self):
        loop = asyncio.get_event_loop()
        self._listen_task = loop.create_task(self._listen_button_evts())
        logger.log(LogLevels.SERVICE_LIFECYCLE, "Service started")
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        tasks = []
        if self._listen_task:
            self._listen_task.cancel()
            tasks.append(self._listen_task)

        if self._copy_task:
            self._copy_task.cancel()
            tasks.append(self._copy_task)

        await asyncio.gather(*tasks, return_exceptions=True)
