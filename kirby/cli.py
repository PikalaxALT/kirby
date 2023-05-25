import argparse
import os
import dotenv
import pathlib
import typing


T = typing.TypeVar('T')


def type_or_none(typ_: type[T]):
    def inner(arg: str | None):
        return None if arg is None else typ_(arg)
    return inner


class CLI(argparse.Namespace):
    dotenv_file: bool | None = None
    token: str | None = None
    command_prefix: str | None = None
    vanilla_rom: pathlib.Path | None = None
    speedchoice_rom: pathlib.Path | None = None
    upr_zx_jar_path: pathlib.Path | None = None
    upr_zx_settings_path: pathlib.Path | None = None
    item_rando_path: pathlib.Path | None = None

    _parser = argparse.ArgumentParser()
    _parser.add_argument(
        '--dotenv',
        dest='dotenv_file',
        type=dotenv.load_dotenv,
        help='Path to a .env file defining the required variables. See kirby.example.env for details.'
    )
    _parser.add_argument(
        '--token',
        dest='token',
        help='Discord auth token.'
    )
    _parser.add_argument(
        '--prefix',
        dest='command_prefix',
        help='Command prefix to use with the bot.'
    )
    _parser.add_argument(
        '--vanilla-rom',
        dest='vanilla_rom',
        type=pathlib.Path,
        help='Path to a vanilla copy of Pokemon Crystal (U)(1.1).'
    )
    _parser.add_argument(
        '--upr-zx-jar',
        dest='upr_zx_jar_path',
        type=pathlib.Path,
        help='Path to the Universal Pokemon Randomizer ZX JAR.'
    )
    _parser.add_argument(
        '--upr-zx-settings',
        dest='upr_zx_settings_path',
        type=pathlib.Path,
        help='Path to the Universal Pokemon Randomizer ZX settings folder.'
    )
    _parser.add_argument(
        '--item-rando',
        dest='item_rando_path',
        type=pathlib.Path,
        help='Path to the item randomizer EXE.'
    )

    def __init__(self, args=None):
        parser = self.__class__._parser
        parser.parse_args(args, self)

        # Update attributes from environment
        maybe_path_converter = type_or_none(pathlib.Path)
        self.token = self.token or os.getenv('KIRBY_DISCORD_TOKEN')
        self.command_prefix = self.command_prefix or os.getenv('KIRBY_COMMAND_PREFIX')
        self.vanilla_rom = self.vanilla_rom or maybe_path_converter(os.getenv('KIRBY_VANILLA_ROM'))
        self.speedchoice_rom = self.speedchoice_rom or maybe_path_converter(os.getenv('KIRBY_SPEEDCHOICE_ROM'))
        self.upr_zx_jar_path = self.upr_zx_jar_path or maybe_path_converter(os.getenv('KIRBY_UPR_ZX'))
        self.upr_zx_settings_path = self.upr_zx_settings_path or maybe_path_converter(os.getenv('KIRBY_UPR_ZX_SETTINGS'))
        self.item_rando_path = self.item_rando_path or maybe_path_converter(os.getenv('KIRBY_ITEM_RANDO_PATH'))

        # Check for missing arguments not supplied by any of the three supported channels
        missing_required_args = {action for action in parser._actions if action.dest not in {'dotenv_file'} and not getattr(self, action.dest)}
        if missing_required_args:
            raise argparse.ArgumentError(None, f'missing required arg(s): {", ".join(missing_required_args)}')
        
        # Check validity of arguments
        missing_paths = {action for action in parser._actions if action.type is pathlib.Path and not getattr(self, action.dest).exists()}
        if missing_paths:
            raise FileNotFoundError(', '.join(missing_paths))
        
        if not (self.item_rando_path / 'Modes').exists():
            raise FileNotFoundError(self.item_rando_path / 'Modes')
        
        if not (self.item_rando_path / 'Pokemon Crystal Item Randomizer.exe').exists():
            raise FileNotFoundError(self.item_rando_path / 'Pokemon Crystal Item Randomizer.exe')
