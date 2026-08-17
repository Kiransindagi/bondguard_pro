from typing import Type

from .in_app import InAppChannel


class ChannelRegistry:
    _channels = {}

    @classmethod
    def register(cls, name: str, channel_class: type):
        cls._channels[name] = channel_class

    @classmethod
    def get_channel(cls, name: str):
        return cls._channels.get(name)

# Register default channels
ChannelRegistry.register("in_app", InAppChannel)
