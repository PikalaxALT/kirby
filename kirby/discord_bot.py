import pathlib
import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from watchdog.events import FileSystemEvent, FileSystemEventHandler, EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED
from watchdog.observers import Observer
from kirby.util.item_rando_caller import ItemRandoCaller
from kirby import __module_dir__

import typing
if typing.TYPE_CHECKING:
    from .cli import CLI


class DiscordBot(commands.Bot):
    def __init__(self, cl_args: 'CLI', rando: ItemRandoCaller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cl_args = cl_args
        self.rando = rando
        self.package_dir = pathlib.Path(__file__).parent

        # Communication with the Quart app
        self.closed = asyncio.Event()

    async def setup_hook(self):
        # Listen for filesystem changes
        # Load extensions
        await asyncio.gather(
            self.add_cog(CoreCog(self)),  # defined below
            *(self.load_extension(
                str(p.relative_to(__module_dir__.parent).with_suffix('')).replace(os.sep, '.')
            ) for p in (__module_dir__ / 'ext').glob('*.py') if p.stem != '__init__')
        )

    async def close(self):
        await super().close()
        self.closed.set()


# Commands to be added to the bot on initial startup
class CoreCog(commands.Cog):
    def __init__(self, bot: 'DiscordBot'):
        self.bot = bot

    @commands.is_owner()
    @commands.hybrid_command('sync')
    async def sync_cmd(self, ctx: commands.Context[DiscordBot]):
        """Sync app commands with all servers"""
        await asyncio.gather(self.bot.tree.sync(), *(self.bot.tree.sync(guild=guild) for guild in self.bot.guilds))
        await ctx.reply('App commands have been updated in all guilds', ephemeral=True)

    @commands.is_owner()
    @commands.hybrid_command('reload')
    async def reload_cmd(self, ctx: commands.Context[DiscordBot], extension: str):
        """Reload an extension. Extension should be of the form `kirby.ext.{name}`."""
        if extension not in self.bot.extensions:
            raise KeyError(f'Extension {extension} not loaded.')
        await self.bot.reload_extension(extension)
        await ctx.reply(f'Reloaded extension {extension}', ephemeral=True)

    @reload_cmd.autocomplete('extension')
    async def reload_extension_autocomplete(self, interaction: discord.Interaction[DiscordBot], current: str):
        return [app_commands.Choice(name=ext, value=ext) for ext in self.bot.extensions if current.lower() in ext.lower()]

    @sync_cmd.error
    @reload_cmd.error
    async def reload_cmd_error(self, ctx: commands.Context[DiscordBot], error: commands.CommandError):
        error = getattr(error, 'original', error)
        await ctx.reply(f'Error: {error}', ephemeral=True)
