"""Denon AVR serial devices of IP"""

import asyncio
import inspect
import logging
import os

from .protocol import Protocol
from .zone import Zone
from .poll import Poll
from .exceptions import DenonPollerAlreadyActive

_LOGGER = logging.getLogger(__name__)


class DenonAVR(object):
    def __init__(self, host=None, port=None, loop=None) -> None:
        super().__init__()

        device_host = host or os.environ.get("DENON_HOST", None)
        device_port = port or os.environ.get("DENON_PORT", None)

        self.__loop = loop or asyncio.get_event_loop()
        self.__zones = dict()

        self.__protocol = Protocol(loop=self.__loop, host=device_host, port=device_port)

        self.__poll = None

    async def connect(self) -> bool:
        ZONES = [1, 2, 3]
        await self.__protocol.connect()
        for zone in ZONES:
            self.__zones[zone] = Zone(
                self.__protocol, zone_number=zone, loop=self.__loop
            )
            await self.__zones[zone].connect()
        return True

    def update(self) -> bool:
        ZONES = [1, 2, 3]
        for zone in ZONES:
            self.__loop.create_task(self.__zones[zone].update())
        return True

    def poll(self, interval) -> None:
        if self.__poll:
            raise DenonPollerAlreadyActive("Poller already loaded")
        self.__poll = Poll(self, self.__loop, interval)
        self.__poll.start()

    @property
    def zone1(self):
        return self.__zones[1]

    @property
    def zone2(self):
        return self.__zones[2]

    @property
    def zone3(self):
        return self.__zones[3]

    async def turn_off(self) -> None:
        """Turn off the Denon unit."""
        await self.__protocol.send("PWSTANDBY")

    async def turn_on(self) -> None:
        """Turn on Denon unit."""
        await self.__protocol.send("PWON")
