"""Denon AVR Zone"""
import asyncio
import inspect
import logging

from ..exceptions import DenonInvalidVolume

_LOGGER = logging.getLogger(__name__)

_DEFAULT_INPUTS = {
    "Phono": "PHONO",
    "CD": "CD",
    "DVD": "DVD",
    "VDP": "VDP",
    "TV": "TV",
    "Satellite": "DBS",
    "VCR-1": "VCR-1",
    "VCR-2": "VCR-2",
    "VCR-3": "VCR-3",
    "Auxiliary Video": "V.AUX",
    "Tape": "CDR/TAPE",
}
_MEDIA_MODES = {"Tuner": "TUNER"}


class Zone(object):
    def __init__(self, protocol, zone_number=1, loop=None) -> None:
        super().__init__()
        self.__loop = loop or asyncio.get_event_loop()
        self.__protocol = protocol
        self.__zone_number = zone_number
        self.__state = "Off"
        self.__volume = 0
        self.__volume_max = 98
        self.__muted = False
        self.__media_source = None
        self.__media_info = None
        self.__source_list = _DEFAULT_INPUTS.copy()
        self.__source_list.update(_MEDIA_MODES)
        if self.auxiliary_zone:
            self.__source_list.update({"Zone 1": "SOURCE"})
        self.__on_change_event_handler = None

    async def __change_event(self) -> None:
        """Fire a notice on change"""
        if not self.__on_change_event_handler:
            return
        if inspect.iscoroutinefunction(self.__on_change_event_handler):
            await self.__on_change_event_handler(self)
        else:
            self.__on_change_event_handler(self)

    def subscribe(self, event_handler) -> None:
        if event_handler:
            self.__on_change_event_handler = event_handler
        else:
            self.__on_change_event_handler = None

    async def connect(self) -> None:
        _LOGGER.debug("Connect %s", self.name)
        self.__protocol.subscribe(self.__process_inbound)
        if self.main_zone:
            await self.__protocol.send("NSFRN ?")
            await self.__protocol.send("SSFUN ?")
            await self.__protocol.send("SSSOD ?")
        await self.update()

    async def update(self) -> None:
        if self.main_zone:
            await self.__protocol.send("PW?")
            await self.__protocol.send("SI?")
            await self.__protocol.send("MV?")
            await self.__protocol.send("CV?")
            await self.__protocol.send("MU?")
            await self.__protocol.send("ZM?")
        else:
            await self.__protocol.send("Z" + str(self.__zone_number) + "MU?")
            await self.__protocol.send("Z" + str(self.__zone_number) + "?")

    async def __process_inbound(self, payload):
        changed = False
        if payload == "PWOFF":
            if self.__state != "Off":
                self.__state = "Off"
                changed = True
                _LOGGER.debug(
                    "Zone %d Unit Power Off. Inbound: %s", self.zone_number, payload
                )
        elif payload == "PWSTANDBY":
            if self.__state != "Off":
                self.__state = "Off"
                changed = True
                _LOGGER.debug(
                    "Zone %d Unit Power Standby. Inbound: %s", self.zone_number, payload
                )
        elif payload.startswith("MVMAX"):
            new_max_volume = int(payload[-2:])
            if self.__volume_max != new_max_volume:
                self.__volume_max = new_max_volume
                changed = True
                _LOGGER.debug(
                    "Zone %d Max Volume Setting. Inbound: %s", self.zone_number, payload
                )
        elif payload.startswith("Z" + str(self.__zone_number)) or (
            self.main_zone and payload.startswith("ZM")
        ):
            data = payload[2:]
            if data == "OFF":
                if self.__state != "Off":
                    self.__state = "Off"
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Power Off. Inbound: %s", self.zone_number, data
                    )
            elif data == "ON":
                if self.__state != "On":
                    self.__state = "On"
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Power On. Inbound: %s", self.zone_number, data
                    )
            elif data.startswith("MU"):
                new_muted_state = True if data[-2:] == "ON" else False
                if self.__muted != new_muted_state:
                    self.__muted = new_muted_state
                    changed = True
                    _LOGGER.debug("Zone %d Mute. Inbound: %s", self.zone_number, data)
            elif data in self.__source_list.values():
                new_media_source = data
                if self.__media_source != new_media_source:
                    self.__media_source = new_media_source
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Media Source. Inbound: %s", self.zone_number, data
                    )
            elif data.isdigit():
                new_volume_raw = int(data)
                if new_volume_raw > self.__volume_max:
                    new_volume = 0
                else:
                    new_volume = new_volume_raw / self.__volume_max
                if self.__volume != new_volume:
                    self.__volume = new_volume
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Set Volume. Inbound: %s", self.zone_number, data
                    )
        elif self.main_zone:
            if payload.startswith("SI") and payload[2:] in self.__source_list.values():
                new_media_source = payload[2:]
                if self.__media_source != new_media_source:
                    self.__media_source = new_media_source
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Media Source. Inbound: %s",
                        self.zone_number,
                        new_media_source,
                    )
            elif payload.startswith("MU"):
                new_mute_state = True if payload[-2:] == "ON" else False
                if self.__muted != new_mute_state:
                    self.__muted = new_mute_state
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Mute. Inbound: %s", self.zone_number, payload[-2:]
                    )
            elif payload.startswith("MV"):
                new_volume_raw = int(payload[-2:])
                if new_volume_raw > self.__volume_max:
                    new_volume = 0
                else:
                    new_volume = new_volume_raw / self.__volume_max
                if self.__volume != new_volume:
                    self.__volume = new_volume
                    changed = True
                    _LOGGER.debug(
                        "Zone %d Set Volume. Inbound: %s",
                        self.zone_number,
                        new_volume_raw,
                    )

        if changed:
            await self.__change_event()

    @property
    def zone_number(self) -> int:
        return self.__zone_number

    @property
    def name(self) -> str:
        if self.main_zone:
            return "Main Zone"
        return "Zone " + str(self.zone_number)

    @property
    def unique_id(self) -> str:
        return "%s:%s/%s" % (self.__protocol.host, self.__protocol.port, self.zone_number)

    @property
    def main_zone(self) -> bool:
        """Is the zone the main zone"""
        if self.__zone_number == 1:
            return True
        return False

    @property
    def auxiliary_zone(self) -> bool:
        """Is the zone not the main zone"""
        if self.__zone_number == 1:
            return False
        return True

    @property
    def state(self) -> str:
        """Is the zone on or off"""
        return self.__state or "Unknown"

    @property
    def volume_level(self) -> int:
        """Zone volume level as percentage"""
        return self.__volume

    @property
    def is_volume_muted(self) -> int:
        """Is the zone muted"""
        return self.__muted

    @property
    def source_list(self) -> list:
        """Return the list of available input sources."""
        return sorted(list(self.__source_list.keys()))

    @property
    def media_title(self) -> str:
        """Return the current media info."""
        return self.__media_info or ""

    @property
    def media_mode(self) -> bool:
        """Is the zone in a media control mode"""
        return self.__media_source in _MEDIA_MODES.values()

    @property
    def source(self) -> str:
        """The current source"""
        for pretty_name, name in self.__source_list.items():
            if self.__media_source == name:
                return pretty_name
        return "Unknown"

    def turn_off(self) -> None:
        """Turn off the zone."""
        if self.main_zone:
            self.__loop.create_task(self.__protocol.send("ZMOFF"))
        else:
            self.__loop.create_task(
                self.__protocol.send("Z" + str(self.__zone_number) + "OFF")
            )

    def turn_on(self) -> None:
        """Turn on the zone."""
        if self.main_zone:
            self.__loop.create_task(self.__protocol.send("ZMON"))
        else:
            self.__loop.create_task(
                self.__protocol.send("Z" + str(self.__zone_number) + "ON")
            )

    def volume_up(self) -> None:
        """Turn up zone volume."""
        if self.main_zone:
            self.__loop.create_task(self.__protocol.send("MVUP"))
        else:
            self.__loop.create_task(
                self.__protocol.send("Z" + str(self.__zone_number) + "UP")
            )

    def volume_down(self) -> None:
        """Turn down zone volume."""
        if self.main_zone:
            self.__loop.create_task(self.__protocol.send("MVDOWN"))
        else:
            self.__loop.create_task(
                self.__protocol.send("Z" + str(self.__zone_number) + "DOWN")
            )

    def set_volume_level(self, volume) -> None:
        """Set zone volume as percentage 0..1"""
        if volume > 1 or volume < 0:
            raise DenonInvalidVolume(
                "Unable to set volume. Must be between 0 and 1.", volume
            )
        if volume == 0:
            set_volume = str(self.__volume_max + 1)
        else:
            set_volume = str(round(volume * self.__volume_max)).zfill(2)

        if self.main_zone:
            self.__loop.create_task(self.__protocol.send("MV" + set_volume))
        else:
            self.__loop.create_task(
                self.__protocol.send("Z" + str(self.__zone_number) + set_volume)
            )

    def mute_volume(self, mute=True) -> None:
        """Mute (true) or unmute (false) media player."""
        if self.main_zone:
            self.__loop.create_task(
                self.__protocol.send("MU" + ("ON" if mute else "OFF"))
            )
        else:
            self.__loop.create_task(
                self.__protocol.send(
                    "Z" + str(self.__zone_number) + "MU" + ("ON" if mute else "OFF")
                )
            )

    def media_play(self):
        """Play media player."""
        self.__loop.create_task(self.__protocol.send("NS9A"))

    def media_pause(self):
        """Pause media player."""
        self.__loop.create_task(self.__protocol.send("NS9B"))

    def media_stop(self):
        """Pause media player."""
        self.__loop.create_task(self.__protocol.send("NS9C"))

    def media_next_track(self):
        """Send the next track command."""
        self.__loop.create_task(self.__protocol.send("NS9D"))

    def media_previous_track(self):
        """Send the previous track command."""
        self.__loop.create_task(self.__protocol.send("NS9E"))

    def select_source(self, source):
        """Select input source."""
        if self.main_zone:
            self.__loop.create_task(
                self.__protocol.send("SI" + self.__source_list.get(source))
            )
        else:
            self.__loop.create_task(
                self.__protocol.send(
                    "Z" + str(self.__zone_number) + self.__source_list.get(source)
                )
            )
