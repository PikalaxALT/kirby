import argparse
import os
import dotenv
import pathlib
import sys
import contextlib


class MISSING(object):
    pass


@contextlib.contextmanager
def traceback_limit(new_limit: int):
    old_limit = getattr(sys, 'tracebacklimit', MISSING)
    sys.tracebacklimit = new_limit
    yield
    if old_limit is MISSING:
        del sys.tracebacklimit
    else:
        sys.tracebacklimit = old_limit


class CLI(argparse.Namespace):
    has_dotenv: bool | None = None
    token: str | None = None
    command_prefix: str | None = None
    vanilla_rom: pathlib.Path | None = None
    speedchoice_rom: pathlib.Path | None = None
    upr_zx_jar_path: pathlib.Path | None = None
    upr_zx_settings_path: pathlib.Path | None = None
    item_rando_path: pathlib.Path | None = None

    def __init__(self, args=None):
        with traceback_limit(0):
            # Use two separate parsers
            # The first parser loads the dotenv file if provided
            # The second parser defines default values using the side effects of the first
            parser_dotenv = argparse.ArgumentParser(add_help=False)
            parser_dotenv.add_argument(
                '--dotenv',
                dest='dotenv_file',
                type=dotenv.load_dotenv,
                help='Path to a .env file defining the required variables. See kirby.example.env for details.'
            )

            _, args = parser_dotenv.parse_known_args(args, self)
            
            parser = argparse.ArgumentParser(parents=[parser_dotenv])  # to document --dotenv in the help message
            parser.add_argument(
                '--token',
                dest='token',
                help='Discord auth token.',
                default=os.getenv('KIRBY_DISCORD_TOKEN')
            )
            parser.add_argument(
                '--prefix',
                dest='command_prefix',
                help='Command prefix to use with the bot.',
                default=os.getenv('KIRBY_COMMAND_PREFIX')
            )
            parser.add_argument(
                '--vanilla-rom',
                dest='vanilla_rom',
                type=pathlib.Path,
                help='Path to a vanilla copy of Pokemon Crystal (U)(1.1).',
                default=os.getenv('KIRBY_VANILLA_ROM')
            )
            parser.add_argument(
                '--speedchoice-rom',
                dest='speedchoice_rom',
                type=pathlib.Path,
                help='Path to a copy of Pokemon Crystal Speedchoice V7 Shopsanity.',
                default=os.getenv('KIRBY_SPEEDCHOICE_ROM')
            )
            parser.add_argument(
                '--upr-zx-jar',
                dest='upr_zx_jar_path',
                type=pathlib.Path,
                help='Path to the Universal Pokemon Randomizer ZX JAR.',
                default=os.getenv('KIRBY_UPR_ZX')
            )
            parser.add_argument(
                '--upr-zx-settings',
                dest='upr_zx_settings_path',
                type=pathlib.Path,
                help='Path to the Universal Pokemon Randomizer ZX settings folder.',
                default=os.getenv('KIRBY_UPR_ZX_SETTINGS')
            )
            parser.add_argument(
                '--item-rando',
                dest='item_rando_path',
                type=pathlib.Path,
                help='Path to the item randomizer EXE.',
                default=os.getenv('KIRBY_ITEM_RANDO_PATH')
            )

            parser.parse_args(args, self)

            # Check for missing arguments not supplied by any of the three supported channels
            if missing_required_args := {action.option_strings[0] for action in parser._actions if action.dest != 'help' and not getattr(self, action.dest)}:
                raise argparse.ArgumentError(None, f'missing required arg(s): {", ".join(missing_required_args)}')
            
            # Check validity of arguments
            if missing_paths := {action for action in parser._actions if action.dest != 'help' and action.type is pathlib.Path and not getattr(self, action.dest).exists()}:
                raise FileNotFoundError(', '.join(missing_paths))
            
            if not (self.item_rando_path / 'Modes').exists():
                raise FileNotFoundError(self.item_rando_path / 'Modes')
            
            if not (self.item_rando_path / 'Pokemon Crystal Item Randomizer.exe').exists():
                raise FileNotFoundError(self.item_rando_path / 'Pokemon Crystal Item Randomizer.exe')
