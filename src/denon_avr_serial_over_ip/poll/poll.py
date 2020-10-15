"""Polling for changes"""
from datetime import timedelta
from ..exceptions import DenonPollerAlreadyActive


class Poll(object):
    def __init__(self, api, loop=None, interval=None) -> None:
        super().__init__()
        self.__api = api
        self.__loop = loop
        self.__active = False
        self.__poller = None

        if not interval:
            self.__interval = timedelta(seconds=60)
        elif not isinstance(interval, timedelta):
            self.__interval = timedelta(seconds=interval)
        else:
            self.__interval = interval

    def start(self):
        self.__poll()

    def __poll(self):
        self.__loop.create_task(self.__async_poll())

    async def __async_poll(self):
        next_poll = self.__loop.time() + self.__interval.total_seconds()
        self.__poller = self.__loop.call_at(next_poll, self.__poll)
        if self.__active:
            raise DenonPollerAlreadyActive("Already polling.")
        self.__active = True
        await self.__api.zone1.update()
        await self.__api.zone2.update()
        await self.__api.zone3.update()
        self.__active = False
