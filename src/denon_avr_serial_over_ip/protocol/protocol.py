"""
Support for Denon AVR 3806 with IP to Serial.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.denonavr3806/
"""
import logging
import asyncio
from time import time

from ..exceptions import DenonCantConnect, DenonNotConnected

_LOGGER = logging.getLogger(__name__)

milliseconds = lambda: int(time() * 1000)


class Protocol(object):
    def __init__(self, loop, host, port) -> None:
        super().__init__()
        self.__loop = loop if loop else asyncio.get_event_loop()
        self.__host = host
        self.__port = port
        self.__session = None
        self.__message_queue = list()
        self.__message_delay = 200
        self.__last_message = None
        self.__receivers = list()
        self.__reader = None
        self.__writer = None
        self.__inbound_task = None
        self.__pending_dequeue = None

    def subscribe(self, event_receiver) -> None:
        if not event_receiver in self.__receivers:
            self.__receivers.append(event_receiver)

    async def send(self, payload=None) -> bool:
        if not payload:
            return
        self.__message_queue.append({"ts": milliseconds(), "payload": payload})
        self.__dequeue()

    async def connect(self) -> bool:
        _LOGGER.debug("Connecting")
        try:
            self.__reader, self.__writer = await asyncio.open_connection(
                self.__host, self.__port
            )
        except OSError:
            return False
        if self.__inbound_task:
            self.__inbound_task.cancel()
            try:
                await self.__inbound_task
            except asyncio.CancelledError:
                _LOGGER.debug("Inbound handler task cancelled")
        self.__inbound_task = asyncio.ensure_future(self.__inbound_handler())
        return True

    async def __inbound_handler(self):
        try:
            while True:
                raw_data = await self.__reader.readuntil(b"\r")
                if raw_data:
                    data = raw_data.decode("ASCII")
                    data = data[:-1]
                    _LOGGER.debug("Received: %s" % data)
                    if self.__receivers:
                        for event_receiver in self.__receivers:
                            self.__loop.create_task(event_receiver(data))
        except asyncio.CancelledError:
            _LOGGER.error("Cancelled inbound handler")
            return

    def __dequeue(self):
        if not self.__message_queue:
            return
        if not self.__writer:
            raise DenonNotConnected

        current_ms = milliseconds()
        if self.__last_message:
            delay_seconds = (
                (self.__last_message + self.__message_delay) - current_ms
            ) / 1000
            if delay_seconds < 0:
                delay_seconds = 0
        else:
            delay_seconds = 0

        if delay_seconds:
            _LOGGER.debug(
                "Waiting: %s (%s)", delay_seconds, self.__message_queue[0]["payload"]
            )
            self.__loop.call_later(delay=delay_seconds, callback=self.__dequeue)
            return False

        message = self.__message_queue.pop(0)
        bytes = bytearray(message["payload"] + "\r", "ASCII")
        self.__writer.write(bytes)
        self.__last_message = current_ms
        _LOGGER.debug("Sent: %s", message["payload"])

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port