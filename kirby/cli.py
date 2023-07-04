import argparse
import os
import dotenv
import pathlib
import platform
import textwrap
import yaml

from kirby import __module_dir__
from kirby.util.traceback_limit import traceback_limit


def wrap_paragraphs(text: str, width: int, indent: str):
    """
    Wrapper around `textwrap.wrap()` which keeps newlines in the input string
    intact.
    """
    lines = list[str]()

    for i in text.splitlines():
        paragraph_lines = \
            textwrap.wrap(i, width, initial_indent=indent, subsequent_indent=indent)

        # `textwrap.wrap()` will return an empty list when passed an empty
        # string (which happens when there are two consecutive line breaks in
        # the input string). This would lead to those line breaks being
        # collapsed into a single line break, effectively removing empty lines
        # from the input. Thus, we add an empty line in that case.
        lines.extend(paragraph_lines or [''])

    return lines


class MyHelpFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        return wrap_paragraphs(text, width, '')

    def _fill_text(self, text, width, indent):
        return '\n'.join(wrap_paragraphs(text, width, indent))


class CLI(argparse.Namespace):
    with open(__module_dir__ / 'snakeconf.yml') as fp:
        snakemake_config = yaml.load(fp, yaml.CSafeLoader)

    has_dotenv: bool | None
    token: str | None
    command_prefix: str | None
    vanilla_rom: pathlib.Path | None = pathlib.Path(snakemake_config['vanilla_rom']).resolve()
    speedchoice_rom: pathlib.Path | None = pathlib.Path(snakemake_config['speedchoice_rom']).resolve()
    upr_zx_jar_path: pathlib.Path | None = pathlib.Path(snakemake_config['zxplus_jar']).resolve()
    upr_zx_settings_path: pathlib.Path | None = pathlib.Path(snakemake_config['zxplus_settings']).resolve()
    item_rando_path: pathlib.Path | None = pathlib.Path(snakemake_config['item_rando']['Windows' if platform.system() == 'Windows' else None]).resolve()
    flips_path: pathlib.Path | None = pathlib.Path(snakemake_config['flips']['Windows' if platform.system() == 'Windows' else None]).resolve()
    webapp_host: str = 'localhost'
    webapp_port: int = 5000

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
                help='Path to a .env file defining the required variables. See kirby.example.env for details.',
                default=dotenv.load_dotenv()
            )

            _, args = parser_dotenv.parse_known_args(args, self)

            parser = argparse.ArgumentParser(
                prog='python -m kirby',
                formatter_class=MyHelpFormatter,
                description='Launch the KIRBY Discord bot to generate key item rando ROMs',
                parents=[parser_dotenv],  # to document --dotenv in the help message
                epilog='Parameter resolution order:\n'
                       '  1. Arguments passed via this interface will take top priority\n'
                       '  2. If --dotenv is passed, any arguments not defined in 1. will be taken from the dotenv file\n'
                       '  3. Otherwise, the same variables defined in the runtime environment will be used\n'
                       '  4. The final fallback value for path-like arguments is what is set in snakeconf.yml.'
            )
            parser.add_argument(
                '--token',
                dest='token',
                help='Discord auth token (.env: KIRBY_DISCORD_TOKEN)',
                default=os.getenv('KIRBY_DISCORD_TOKEN')
            )
            parser.add_argument(
                '--prefix',
                dest='command_prefix',
                help='Command prefix to use with the bot (.env: KIRBY_COMMAND_PREFIX)',
                default=os.getenv('KIRBY_COMMAND_PREFIX')
            )
            parser.add_argument(
                '--vanilla-rom',
                dest='vanilla_rom',
                type=pathlib.Path,
                help='Path to a vanilla copy of Pokemon Crystal (U)(1.1) (.env: KIRBY_VANILLA_ROM)',
                default=pathlib.Path(os.getenv(
                    'KIRBY_VANILLA_ROM',
                    CLI.vanilla_rom
                )).resolve()
            )
            parser.add_argument(
                '--speedchoice-rom',
                dest='speedchoice_rom',
                type=pathlib.Path,
                help='Path to a copy of Pokemon Crystal Speedchoice V7 Shopsanity (.env: KIRBY_SPEEDCHOICE_ROM)',
                default=pathlib.Path(os.getenv(
                    'KIRBY_SPEEDCHOICE_ROM',
                    CLI.speedchoice_rom
                )).resolve()
            )
            parser.add_argument(
                '--upr-zx-jar',
                dest='upr_zx_jar_path',
                type=pathlib.Path,
                help='Path to the Universal Pokemon Randomizer ZX JAR (.env: KIRBY_UPR_ZX_JAR)',
                default=pathlib.Path(os.getenv(
                    'KIRBY_UPR_ZX_JAR',
                    CLI.upr_zx_jar_path
                )).resolve()
            )
            parser.add_argument(
                '--upr-zx-settings',
                dest='upr_zx_settings_path',
                type=pathlib.Path,
                help='Path to the Universal Pokemon Randomizer ZX settings folder (.env: KIRBY_UPR_ZX_SETTINGS)',
                default=pathlib.Path(os.getenv(
                    'KIRBY_UPR_ZX_SETTINGS',
                    CLI.upr_zx_settings_path
                ))
            )
            parser.add_argument(
                '--item-rando',
                dest='item_rando_path',
                type=pathlib.Path,
                help='Path to the folder containing the item randomizer CLI and modes (.env: KIRBY_ITEM_RANDO_PATH)',
                default=pathlib.Path(os.getenv(
                    'KIRBY_ITEM_RANDO_PATH',
                    CLI.item_rando_path
                )).resolve()
            )
            parser.add_argument(
                '--flips',
                dest='flips_path',
                type=pathlib.Path,
                help='Path to the Floating IPS binary (.env: KIRBY_FLOATING_IPS)',
                default=pathlib.Path(os.getenv(
                    'KIRBY_FLOATING_IPS',
                    CLI.flips_path
                )).resolve()
            )
            parser.add_argument(
                '--webapp-host',
                dest='webapp_host',
                help='Address from which to host the web app (.env: KIRBY_WEBAPP_HOST)',
                default=os.getenv(
                    'KIRBY_WEBAPP_HOST',
                    'localhost'
                )
            )
            parser.add_argument(
                '--webapp-port',
                dest='webapp_port',
                help='Port over which to host the web app (.env: KIRBY_WEBAPP_PORT)',
                default=int(os.getenv(
                    'KIRBY_WEBAPP_PORT',
                    '5000'
                ))
            )

            parser.parse_args(args, self)

            # Check for missing arguments not supplied by any of the three supported channels
            if missing_required_args := {action.option_strings[0] for action in parser._actions if action.dest in {'command_prefix', 'token'} and not getattr(self, action.dest)}:
                raise argparse.ArgumentError(None, f'missing required arg(s): {", ".join(missing_required_args)}')

            # # Check validity of arguments
            # if missing_paths := {action for action in parser._actions if action.dest != 'help' and action.type is pathlib.Path and not getattr(self, action.dest).exists()}:
            #     raise FileNotFoundError(', '.join(missing_paths))

            # if not (self.item_rando_path / 'Modes').exists():
            #     raise FileNotFoundError(self.item_rando_path / 'Modes')

            # if not (self.item_rando_path / 'Pokemon Crystal Item Randomizer.exe').exists():
            #     raise FileNotFoundError(self.item_rando_path / 'Pokemon Crystal Item Randomizer.exe')
