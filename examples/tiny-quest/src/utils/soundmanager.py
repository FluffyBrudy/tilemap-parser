from pathlib import Path
from typing import Dict, Literal

import pygame
from pygame import Channel, Sound


class SoundManager:
    main_channels = (0, 1)
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        if pygame.mixer.get_init() is None:
            raise Exception("Channels not initialize")

        self._sfx: Dict[str, Sound] = {}
        self._bg: Dict[str, Sound] = {}

        self.max_channels = pygame.mixer.get_num_channels()
        self._channels = tuple([pygame.Channel(i) for i in range(self.max_channels)])
        self._next_sfx_channel = len(self.main_channels)

    def add_sound(self, audio_path: Path, ref_key: str, stype: Literal["sfx", "main"]) -> bool:
        """Adds sound , either sfx or main sound"""
        scope = self._bg if stype == "main" else self._sfx
        try:
            scope[ref_key] = pygame.Sound(audio_path)
            return True
        except FileExistsError:
            print(f"Path doesnt exists for sound ${ref_key}")
            return False
        except TypeError:
            print(f"audio path must be PathLike, not ${type(audio_path)}")
            return False
        except Exception as e:
            print(f"Failed to load sound: {e}")
            return False

    def play(self, ref_key: str, stype: Literal["sfx", "main"]) -> None:
        sounds = self._bg if stype == "main" else self._sfx

        sound = sounds.get(ref_key)
        if sound is None:
            raise KeyError(f"Unknown sound '{ref_key}'")

        channel = self.__assign_channel(stype)
        channel.play(sound)

    def __assign_channel(self, stype: Literal["sfx", "main"]) -> Channel:
        """Return an appropriate channel for playback."""

        if stype == "main":
            for idx in self.main_channels:
                channel = self._channels[idx]
                if not channel.get_busy():
                    return channel

            channel = self._channels[self.main_channels[0]]
            channel.stop()
            return channel

        for channel in self._channels[len(self.main_channels) :]:
            if not channel.get_busy():
                return channel

        channel = self._channels[self._next_sfx_channel]
        channel.stop()

        self._next_sfx_channel += 1
        if self._next_sfx_channel >= self.max_channels:
            self._next_sfx_channel = len(self.main_channels)

        return channel


soundmanager = SoundManager()
