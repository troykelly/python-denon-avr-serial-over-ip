# Python Library for Denon AVR Serial over IP Control

![PyPI](https://github.com/troykelly/python-denon-avr-serial-over-ip/workflows/Publish%20Python%20%F0%9F%90%8D%20distributions%20%F0%9F%93%A6%20to%20PyPI%20and%20TestPyPI/badge.svg?branch=main) [![GitHub issues](https://img.shields.io/github/issues/troykelly/python-denon-avr-serial-over-ip?style=plastic)](https://github.com/troykelly/python-denon-avr-serial-over-ip/issues) [![GitHub forks](https://img.shields.io/github/forks/troykelly/python-denon-avr-serial-over-ip?style=plastic)](https://github.com/troykelly/python-denon-avr-serial-over-ip/network) [![GitHub stars](https://img.shields.io/github/stars/troykelly/python-denon-avr-serial-over-ip?style=plastic)](https://github.com/troykelly/python-denon-avr-serial-over-ip/stargazers) [![GitHub license](https://img.shields.io/github/license/troykelly/python-denon-avr-serial-over-ip?style=plastic)](https://github.com/troykelly/python-denon-avr-serial-over-ip/blob/main/LICENSE.txt) [![Twitter](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fpython-denon-avr-serial-over-ip)](https://twitter.com/intent/tweet?url=https%3A%2F%2Fgithub.com%2Ftroykelly%2Fpython-denon-avr-serial-over-ip&via=troykelly&text=Control%20older%20Denon%20AVR%20models%20via%20their%20serial%20port%20over%20IP%20%23api%23homeautomation)

## Description

Connects to an older Denon AVR serial port using an IP to Serial convertor

### Note

This is in no way affiliated with Denon.

### Issues

I don't have access to a Denon AMP any more directly - so most of this is from old Protocol documentation

### Logging / Debugging

This library uses `logging` just set the log level and format you need.

## Example

The examples below may look a little complex - because this library relies on functions like `.connect()` need to be `await`ed.

### Connect and turn on Zone 2

```python
import asyncio
from denon_avr_serial_over_ip import DenonAVR

api = DenonAVR(
        host=10.10.10.10,
        longitude=5001,
    )

async def zone_change(zone):
    """Alert about a zone change"""
    _LOGGER.info("Zone %s changed", zone.zone_number)

async def connect_turn_on_z2():
    await API.connect()
    API.zone2.subscribe(zone_change)
    await asyncio.sleep(2)
    await API.zone2.turn_on()
    await asyncio.sleep(2)
    await API.zone2.set_volume_level(0.5)
    await asyncio.sleep(2)
    await API.turn_off()

asyncio.get_event_loop().run_until_complete(connect_turn_on_z2())
```

## Support

<a href="https://www.buymeacoffee.com/troykelly" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
