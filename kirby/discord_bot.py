import pathlib
import os
import asyncio
from discord.ext import commands
from . import __module_dir__

import typing
if typing.TYPE_CHECKING:
    from .cli import CLI


class DiscordBot(commands.Bot):
    def __init__(self, cl_args: 'CLI', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cl_args = cl_args
        self.package_dir = pathlib.Path(__file__).parent

        # Prepopulate choices
        self.upr_settings_files = set(self.cl_args.upr_zx_settings_path.glob('*.rnqs'))
        self.item_rando_presets = set(self.cl_args.item_rando_path.parent.glob('Modes/*.yml'))

    async def setup_hook(self):
        await asyncio.gather(*(self.load_extension(str(p.relative_to(__module_dir__.parent).with_suffix('')).replace(os.sep, '.')) for p in (__module_dir__ / 'ext').glob('*.py') if p.stem != '__init__'))
