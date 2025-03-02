from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusPropertyEmitsChangeFlag,
    DbusUnprivilegedFlag,
    dbus_method_async,
    dbus_property_async,
)


class Manager(DbusInterfaceCommonAsync, interface_name="org.freedesktop.UDisks2.Manager"):
    @dbus_method_async(
        input_signature="s",
        result_signature="(bs)",
        result_args_names=("available",),
        flags=DbusUnprivilegedFlag,
    )
    async def can_format(self, type: str) -> Tuple[bool, str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="(bts)",
        result_args_names=("available",),
        flags=DbusUnprivilegedFlag,
    )
    async def can_resize(self, type: str) -> Tuple[bool, int, str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="(bs)",
        result_args_names=("available",),
        flags=DbusUnprivilegedFlag,
    )
    async def can_check(self, type: str) -> Tuple[bool, str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="(bs)",
        result_args_names=("available",),
        flags=DbusUnprivilegedFlag,
    )
    async def can_repair(self, type: str) -> Tuple[bool, str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="ha{sv}",
        result_signature="o",
        result_args_names=("resulting_device",),
        flags=DbusUnprivilegedFlag,
    )
    async def loop_setup(self, fd: int, options: Dict[str, Tuple[str, Any]]) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="aossta{sv}",
        result_signature="o",
        result_args_names=("resulting_array",),
        flags=DbusUnprivilegedFlag,
    )
    async def mdraid_create(
        self,
        blocks: List[str],
        level: str,
        name: str,
        chunk: int,
        options: Dict[str, Tuple[str, Any]],
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(input_signature="sb", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def enable_module(self, name: str, enable: bool) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="ao",
        result_args_names=("block_objects",),
        flags=DbusUnprivilegedFlag,
    )
    async def get_block_devices(self, options: Dict[str, Tuple[str, Any]]) -> List[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}a{sv}",
        result_signature="ao",
        result_args_names=("devices",),
        flags=DbusUnprivilegedFlag,
    )
    async def resolve_device(
        self, devspec: Dict[str, Tuple[str, Any]], options: Dict[str, Tuple[str, Any]]
    ) -> List[str]:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def version(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="as", flags=DbusPropertyEmitsChangeFlag)
    def supported_filesystems(self) -> List[str]:
        raise NotImplementedError

    @dbus_property_async(property_signature="as", flags=DbusPropertyEmitsChangeFlag)
    def supported_encryption_types(self) -> List[str]:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def default_encryption_type(self) -> str:
        raise NotImplementedError


class Drive(DbusInterfaceCommonAsync, interface_name="org.freedesktop.UDisks2.Drive"):
    @dbus_method_async(input_signature="a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def eject(self, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag
    )
    async def set_configuration(
        self, value: Dict[str, Tuple[str, Any]], options: Dict[str, Tuple[str, Any]]
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(input_signature="a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def power_off(self, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def vendor(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def model(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def revision(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def serial(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def wwn(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="a{sv}", flags=DbusPropertyEmitsChangeFlag)
    def configuration(self) -> Dict[str, Tuple[str, Any]]:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def media(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="as", flags=DbusPropertyEmitsChangeFlag)
    def media_compatibility(self) -> List[str]:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def media_removable(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def media_available(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def media_change_detected(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="t", flags=DbusPropertyEmitsChangeFlag)
    def size(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="t", flags=DbusPropertyEmitsChangeFlag)
    def time_detected(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="t", flags=DbusPropertyEmitsChangeFlag)
    def time_media_detected(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def optical(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def optical_blank(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="u", flags=DbusPropertyEmitsChangeFlag)
    def optical_num_tracks(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="u", flags=DbusPropertyEmitsChangeFlag)
    def optical_num_audio_tracks(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="u", flags=DbusPropertyEmitsChangeFlag)
    def optical_num_data_tracks(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="u", flags=DbusPropertyEmitsChangeFlag)
    def optical_num_sessions(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="i", flags=DbusPropertyEmitsChangeFlag)
    def rotation_rate(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def connection_bus(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def seat(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def removable(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def ejectable(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def sort_key(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def can_power_off(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def sibling_id(self) -> str:
        raise NotImplementedError


class FilesystemMixin(
    DbusInterfaceCommonAsync, interface_name="org.freedesktop.UDisks2.Filesystem"
):
    @dbus_method_async(input_signature="sa{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def set_label(self, label: str, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_method_async(input_signature="sa{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def set_uuid(self, uuid: str, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="s",
        result_args_names=("mount_path",),
        flags=DbusUnprivilegedFlag,
    )
    async def mount(self, options: Dict[str, Tuple[str, Any]]) -> str:
        raise NotImplementedError

    @dbus_method_async(input_signature="a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def unmount(self, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_method_async(input_signature="ta{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def resize(self, size: int, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="b",
        result_args_names=("consistent",),
        flags=DbusUnprivilegedFlag,
    )
    async def check(self, options: Dict[str, Tuple[str, Any]]) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="b",
        result_args_names=("repaired",),
        flags=DbusUnprivilegedFlag,
    )
    async def repair(self, options: Dict[str, Tuple[str, Any]]) -> bool:
        raise NotImplementedError

    @dbus_method_async(input_signature="a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def take_ownership(self, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_property_async(property_signature="aay", flags=DbusPropertyEmitsChangeFlag)
    def mount_points(self) -> List[bytes]:
        raise NotImplementedError

    @property
    async def mount_point(self) -> str | None:
        mnt_pnts = [it.decode().removesuffix("\x00") for it in await self.mount_points]
        return mnt_pnts[0] if mnt_pnts else None


class Block(DbusInterfaceCommonAsync, interface_name="org.freedesktop.UDisks2.Block"):
    @dbus_method_async(
        input_signature="(sa{sv})a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag
    )
    async def add_configuration_item(
        self, item: Tuple[str, Dict[str, Tuple[str, Any]]], options: Dict[str, Tuple[str, Any]]
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="(sa{sv})a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag
    )
    async def remove_configuration_item(
        self, item: Tuple[str, Dict[str, Tuple[str, Any]]], options: Dict[str, Tuple[str, Any]]
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="(sa{sv})(sa{sv})a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag
    )
    async def update_configuration_item(
        self,
        old_item: Tuple[str, Dict[str, Tuple[str, Any]]],
        new_item: Tuple[str, Dict[str, Tuple[str, Any]]],
        options: Dict[str, Tuple[str, Any]],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="a(sa{sv})",
        result_args_names=("configuration",),
        flags=DbusUnprivilegedFlag,
    )
    async def get_secret_configuration(
        self, options: Dict[str, Tuple[str, Any]]
    ) -> List[Tuple[str, Dict[str, Tuple[str, Any]]]]:
        raise NotImplementedError

    @dbus_method_async(input_signature="sa{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def format(self, type: str, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="h",
        result_args_names=("fd",),
        flags=DbusUnprivilegedFlag,
    )
    async def open_for_backup(self, options: Dict[str, Tuple[str, Any]]) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="h",
        result_args_names=("fd",),
        flags=DbusUnprivilegedFlag,
    )
    async def open_for_restore(self, options: Dict[str, Tuple[str, Any]]) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="a{sv}",
        result_signature="h",
        result_args_names=("fd",),
        flags=DbusUnprivilegedFlag,
    )
    async def open_for_benchmark(self, options: Dict[str, Tuple[str, Any]]) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sa{sv}",
        result_signature="h",
        result_args_names=("fd",),
        flags=DbusUnprivilegedFlag,
    )
    async def open_device(self, mode: str, options: Dict[str, Tuple[str, Any]]) -> int:
        raise NotImplementedError

    @dbus_method_async(input_signature="a{sv}", result_args_names=(), flags=DbusUnprivilegedFlag)
    async def rescan(self, options: Dict[str, Tuple[str, Any]]) -> None:
        raise NotImplementedError

    @dbus_property_async(property_signature="ay", flags=DbusPropertyEmitsChangeFlag)
    def device(self) -> bytes:
        raise NotImplementedError

    @dbus_property_async(property_signature="ay", flags=DbusPropertyEmitsChangeFlag)
    def preferred_device(self) -> bytes:
        raise NotImplementedError

    @dbus_property_async(property_signature="aay", flags=DbusPropertyEmitsChangeFlag)
    def symlinks(self) -> List[bytes]:
        raise NotImplementedError

    @dbus_property_async(property_signature="t", flags=DbusPropertyEmitsChangeFlag)
    def device_number(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="t", flags=DbusPropertyEmitsChangeFlag)
    def size(self) -> int:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def read_only(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="o", flags=DbusPropertyEmitsChangeFlag)
    def drive(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="o", flags=DbusPropertyEmitsChangeFlag)
    def mdraid(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="o", flags=DbusPropertyEmitsChangeFlag)
    def mdraid_member(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id_usage(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id_type(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id_version(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id_label(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def id_uuid(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="a(sa{sv})", flags=DbusPropertyEmitsChangeFlag)
    def configuration(self) -> List[Tuple[str, Dict[str, Tuple[str, Any]]]]:
        raise NotImplementedError

    @dbus_property_async(property_signature="o", flags=DbusPropertyEmitsChangeFlag)
    def crypto_backing_device(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def hint_partitionable(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def hint_system(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def hint_ignore(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="b", flags=DbusPropertyEmitsChangeFlag)
    def hint_auto(self) -> bool:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def hint_name(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def hint_icon_name(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def hint_symbolic_icon_name(self) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="as", flags=DbusPropertyEmitsChangeFlag)
    def userspace_mount_options(self) -> List[str]:
        raise NotImplementedError


class PartitionTable(
    DbusInterfaceCommonAsync, interface_name="org.freedesktop.UDisks2.PartitionTable"
):
    @dbus_method_async(
        input_signature="ttssa{sv}",
        result_signature="o",
        result_args_names=("created_partition",),
        flags=DbusUnprivilegedFlag,
    )
    async def create_partition(
        self, offset: int, size: int, type: str, name: str, options: Dict[str, Tuple[str, Any]]
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="ttssa{sv}sa{sv}",
        result_signature="o",
        result_args_names=("created_partition",),
        flags=DbusUnprivilegedFlag,
    )
    async def create_partition_and_format(
        self,
        offset: int,
        size: int,
        type: str,
        name: str,
        options: Dict[str, Tuple[str, Any]],
        format_type: str,
        format_options: Dict[str, Tuple[str, Any]],
    ) -> str:
        raise NotImplementedError

    @dbus_property_async(property_signature="ao", flags=DbusPropertyEmitsChangeFlag)
    def partitions(self) -> List[str]:
        raise NotImplementedError

    @dbus_property_async(property_signature="s", flags=DbusPropertyEmitsChangeFlag)
    def type(self) -> str:
        raise NotImplementedError


class PartitionBlock(Block, PartitionTable): ...


class Filesystem(Block, FilesystemMixin): ...
