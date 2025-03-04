import asyncio
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
from evdev import list_devices as list_evdev, InputDevice

from onetouchcopy.service import Udisks2Manager, Service
from onetouchcopy.utils import await_sig, LogLevels

KERNEL_MODULE_NAME = "qnap8528"
DEST_ENV_VAR = "DEST"


async def start():
    parser = ArgumentParser(
        prog="Qnap's one touch copy feature for Linux",
        description=dedent("""
        Daemon watching Qnap's copy button events to copy the content of any disk plugged into
        that USB port.
        """),
    )

    parser.add_argument(
        "-d",
        "--destination",
        help=(
            "Directory were to copy the content of the USB disk; "
            f"will take priority over {DEST_ENV_VAR} environment variable"
        ),
        action="store",
        type=str,
    )

    parser.add_argument(
        "-c", "--config", help="Configuration file", action="store", default="/etc/onetouchcopy"
    )

    parser.add_argument("--verbose", "-v", action="count", default=0)

    args = parser.parse_args()

    logging.addLevelName(LogLevels.SERVICE_LIFECYCLE.value, LogLevels.SERVICE_LIFECYCLE.name)
    logger_config = {
        "handlers": (logging.StreamHandler(sys.stdout),),
        "force": True,
        "level": LogLevels.SERVICE_LIFECYCLE,
    }
    if args.verbose == 1:
        logger_config["level"] = logging.DEBUG
    elif args.verbose >= 2:
        logger_config["level"] = logging.NOTSET

    logging.basicConfig(**logger_config)
    logger = logging.getLogger("One touch copy daemon")

    if not os.path.exists(args.config):
        logger.warning(f"Config {args.config} file not found")
    else:
        load_dotenv(args.config)

    try:
        device = next(
            device
            for path in list_evdev()
            if (device := InputDevice(path)).name == KERNEL_MODULE_NAME
        )
    except StopIteration:
        logger.critical(f"Firmware {KERNEL_MODULE_NAME} couldn't be found on the device")
        return 1

    destination = args.destination or os.getenv(DEST_ENV_VAR)

    if not destination:
        logger.critical(
            f"Destination path not set. Please use -d option or the {DEST_ENV_VAR} environment "
            "variable. Use --help for more information."
        )
        return 1

    path = Path(destination)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.critical(f"Destination directory {path} is not writable")
        return 1

    async with Udisks2Manager() as manager, Service(device, manager, path):
        await await_sig()

    logger.log(LogLevels.SERVICE_LIFECYCLE, "Service stopped")

    return 0


def main():
    raise SystemExit(asyncio.get_event_loop().run_until_complete(start()))


if __name__ == "__main__":
    main()
