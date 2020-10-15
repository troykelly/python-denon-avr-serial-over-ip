"""Denon AVR Exceptions"""


class Error(Exception):
    pass


class DenonCantConnect(Error):
    def __init__(self, message) -> None:
        super().__init__()
        self.message = message


class DenonNotConnected(Error):
    def __init__(self, message) -> None:
        super().__init__()
        self.message = message


class DenonInvalidVolume(Error):
    def __init__(self, message, volume=None) -> None:
        super().__init__()
        self.message = message
        self.volume = volume


class DenonPollerAlreadyActive(Error):
    def __init__(self, message) -> None:
        super().__init__()
        self.message = message
