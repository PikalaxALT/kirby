import pathlib
import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from watchdog.events import FileSystemEvent, FileSystemEventHandler, EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED
from watchdog.observers import Observer
from kirby import __module_dir__

import typing
if typing.TYPE_CHECKING:
    from .cli import CLI

_T = typing.TypeVar('_T')


class Watchdog(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue[FileSystemEvent], loop: asyncio.BaseEventLoop, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue
        self._loop = loop

    def on_any_event(self, event: FileSystemEvent):
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)


class EventIterator(object):
    def __init__(self, queue: asyncio.Queue[FileSystemEvent],
                 loop: asyncio.BaseEventLoop | None = None):
        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self.queue.get()

        if item is None:
            raise StopAsyncIteration

        return item


def is_settings_file(child: pathlib.Path, parent: pathlib.Path, ext: str):
    return child.is_relative_to(parent) and child.suffix == ext


class DiscordBot(commands.Bot):
    def __init__(self, cl_args: 'CLI', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cl_args = cl_args
        self.package_dir = pathlib.Path(__file__).parent

        self.settings_file_specs = (
            (self.cl_args.upr_zx_settings_path, '.rnqs'),
            (self.cl_args.item_rando_path.parent / 'Modes', '.yml'),
        )

        # Prepopulate choices
        self.settings_files = {
            parent: set(parent.glob(f'*{ext}'))
            for parent, ext in self.settings_file_specs
        }

        # Communication with the Quart app
        self.closed = asyncio.Event()

    @property
    def upr_settings_files(self):
        return self.settings_files[self.cl_args.upr_zx_settings_path]

    @property
    def item_rando_presets(self):
        return self.settings_files[self.cl_args.item_rando_path.parent / 'Modes']

    def watch(self):
        handler = Watchdog(self._path_queue, self.loop)
        observer = Observer()
        observer.schedule(handler, self.cl_args.upr_zx_settings_path, recursive=False)
        observer.schedule(handler, self.cl_args.item_rando_path / 'Modes', recursive=False)
        observer.join()

    def handle_file_create(self, path_s: str):
        path = pathlib.Path(path_s)
        self.settings_files[path.parent].add(path)

    def handle_file_delete(self, path_s: str):
        path = pathlib.Path(path_s)
        self.settings_files[path.parent].discard(path)

    async def sync_presets(self):
        fut = asyncio.create_task(asyncio.to_thread(self.watch))
        try:
            async for event in EventIterator(self._path_queue):
                if event.event_type == EVENT_TYPE_MOVED:
                    self.handle_file_delete(event.src_path)
                    self.handle_file_create(event.dest_path)
                elif event.event_type == EVENT_TYPE_CREATED:
                    self.handle_file_create(event.src_path)
                elif event.event_type == EVENT_TYPE_DELETED:
                    self.handle_file_delete(event.src_path)
        finally:
            fut.cancel()

    async def setup_hook(self):
        # Listen for filesystem changes
        self._path_queue: asyncio.Queue[FileSystemEvent] = asyncio.Queue()
        self.filesystem_listener_task = asyncio.create_task(self.sync_presets())

        # Load extensions
        await asyncio.gather(
            self.add_cog(CoreCog(self)),  # defined below
            *(self.load_extension(
                str(p.relative_to(__module_dir__.parent).with_suffix('')).replace(os.sep, '.')
            ) for p in (__module_dir__ / 'ext').glob('*.py') if p.stem != '__init__')
        )

    async def close(self):
        await self._path_queue.put(None)
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
