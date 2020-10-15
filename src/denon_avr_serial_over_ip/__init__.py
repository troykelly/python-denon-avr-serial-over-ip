# -*- coding: utf-8 -*-
from pkg_resources import get_distribution, DistributionNotFound
from .main import DenonAVR

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "denon-avr-serial-over-ip"
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound
