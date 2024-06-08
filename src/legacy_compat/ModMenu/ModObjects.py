# ruff: noqa: N802, N803, D102, D103, N999

from __future__ import annotations

import copy
from abc import ABCMeta
from dataclasses import dataclass
from enum import Enum, Flag, IntEnum, auto
from typing import TYPE_CHECKING, Any

from mods_base import (
    AbstractCommand,
    BaseOption,
    Game,
    HookProtocol,
    KeybindType,
    Mod,
    ModType,
    deregister_mod,
    register_mod,
)

from . import Options

if TYPE_CHECKING:
    from collections.abc import Sequence

# TODO: SettingsInputs
# TODO: Keybinds
# TODO: Networking
# TODO: Hooks

__all__: tuple[str, ...] = (
    "EnabledSaveType",
    "Game",
    "ModPriorities",
    "Mods",
    "ModTypes",
    "RegisterMod",
    "SDKMod",
)


# Wrapper class to auto register the new mod object when a legacy mod is added to the list
class _LegacyModList(list["SDKMod"]):
    def append(self, mod: SDKMod) -> None:
        super().append(mod)
        register_mod(mod.new_mod_obj)

    def remove(self, mod: SDKMod) -> None:
        super().remove(mod)
        deregister_mod(mod.new_mod_obj)


Mods = _LegacyModList()  # pyright: ignore[reportGeneralTypeIssues]


def RegisterMod(mod: SDKMod) -> None:
    Mods.append(mod)


class ModPriorities(IntEnum):
    High = 10
    Standard = 0
    Low = -10
    Library = Low


class ModTypes(Flag):
    NONE = 0
    Utility = auto()
    Content = auto()
    Gameplay = auto()
    Library = auto()
    All = Utility | Content | Gameplay | Library


class EnabledSaveType(Enum):
    NotSaved = auto()
    LoadWithSettings = auto()
    LoadOnMainMenu = auto()


@dataclass
class _NewMod(Mod):
    legacy_mod: _LegacyMod = None  # type: ignore

    @property
    def name(self) -> str:
        return self.legacy_mod.Name

    @name.setter
    def name(self, val: str) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self.legacy_mod.Name = val

    @property
    def author(self) -> str:
        return self.legacy_mod.Author

    @author.setter
    def author(self, val: str) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self.legacy_mod.Author = val

    @property
    def description(self) -> str:
        return self.legacy_mod.Description

    @description.setter
    def description(self, val: str) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self.legacy_mod.Description = val

    @property
    def version(self) -> str:
        return self.legacy_mod.Version

    @version.setter
    def version(self, val: str) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self.legacy_mod.Version = val

    @property
    def mod_type(self) -> ModType:
        return (
            ModType.Library
            if self.legacy_mod.Priority <= ModPriorities.Library
            else ModType.Standard
        )

    @mod_type.setter
    def mod_type(self, val: ModType) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        match val:
            case ModType.Standard:
                self.legacy_mod.Priority = ModPriorities.Standard
            case ModType.Library:
                self.legacy_mod.Priority = ModPriorities.Library

    @property
    def supported_games(self) -> Game:
        return self.legacy_mod.SupportedGames

    @supported_games.setter
    def supported_games(self, val: Game) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self.legacy_mod.SupportedGames = val

    # TODO
    keybinds: Sequence[KeybindType] = ()

    @property
    def options(self) -> Sequence[BaseOption]:
        return [
            Options.convert_to_new_style_option(option, self.legacy_mod)
            for option in self.legacy_mod.Options
        ]

    @options.setter
    def options(self, val: Sequence[BaseOption]) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        raise NotImplementedError("Unable to set options on legacy sdk mod")

    # TODO
    hooks: Sequence[HookProtocol] = ()

    commands: Sequence[AbstractCommand] = ()

    @property
    def auto_enable(self) -> bool:
        return self.legacy_mod.SaveEnabledState != EnabledSaveType.NotSaved

    @auto_enable.setter
    def auto_enable(self, val: bool) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self.legacy_mod.SaveEnabledState = (
            EnabledSaveType.LoadWithSettings if val else EnabledSaveType.NotSaved
        )

    def __init__(self, legacy_mod: _LegacyMod) -> None:
        self.legacy_mod = legacy_mod
        super().__post_init__()

    def get_status(self) -> str:
        if Game.get_current() not in self.supported_games:
            return "<font color='#ffff00'>Incompatible</font>"

        match self.legacy_mod.Status:
            case None:
                if self.is_enabled:
                    return "<font color='#00ff00'>Enabled</font>"
                return "<font color='#ff0000'>Disabled</font>"
            case "Enabled":
                return "<font color='#00ff00'>Enabled</font>"
            case "Disabled":
                return "<font color='#ff0000'>Disabled</font>"
            case _:
                return self.legacy_mod.Status


class _LegacyModMeta(ABCMeta):
    legacy_clone_attributes: tuple[str, ...] = (
        "Author",
        "Description",
        "Version",
        "SupportedGames",
        "Types",
        "Priority",
        "SaveEnabledState",
        "Status",
        # "SettingsInputs",
        "Options",
        # "Keybinds",
        # "_server_functions",
        # "_client_functions",
        "_is_enabled",
    )

    def __init__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any], /) -> None:
        super().__init__(name, bases, attrs)

        for name in _LegacyModMeta.legacy_clone_attributes:
            setattr(cls, name, copy.copy(getattr(cls, name)))

    def __call__(cls, *args: Any, **kwargs: Any) -> _LegacyMod:
        instance: _LegacyMod = super().__call__(*args, **kwargs)
        instance.new_mod_obj = _NewMod(instance)
        return instance


class _LegacyMod(metaclass=_LegacyModMeta):
    Name: str
    Author: str = "Unknown"
    Description: str = ""
    Version: str = "Unknown Version"

    SupportedGames: Game = Game.BL2 | Game.TPS | Game.AoDK
    Types: ModTypes = ModTypes.NONE
    Priority: int = ModPriorities.Standard
    SaveEnabledState: EnabledSaveType = EnabledSaveType.NotSaved

    Status: str | None = None
    # SettingsInputs: dict[str, str] = {"Enter": "Enable"}
    Options: Sequence[Options.Base] = []
    # Keybinds: Sequence[KeybindManager.Keybind] = []

    # _server_functions: Set[Callable[..., None]] = set()
    # _client_functions: Set[Callable[..., None]] = set()

    _is_enabled: bool | None = None

    new_mod_obj: _NewMod

    @property
    def IsEnabled(self) -> bool:
        return self.new_mod_obj.is_enabled

    @IsEnabled.setter
    def IsEnabled(self, val: bool) -> None:
        self.new_mod_obj.is_enabled = val

    def Enable(self) -> None:
        self.new_mod_obj.enable()

    def Disable(self) -> None:
        self.new_mod_obj.disable()

    # def SettingsInputPressed(self, action: str) -> None:
    #     pass
    # def GameInputPressed(self, bind: KeybindManager.Keybind, event: KeybindManager.InputEvent) -> None:
    #     pass

    def ModOptionChanged(self, option: Options.Base, new_value: Any) -> None:
        pass

    # @staticmethod
    # def NetworkSerialize(arguments: NetworkManager.NetworkArgsDict) -> str:
    #     pass

    # @staticmethod
    # def NetworkDeserialize(serialized: str) -> NetworkManager.NetworkArgsDict:
    #     pass


SDKMod = _LegacyMod