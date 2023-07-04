import asyncio
import platform
import tempfile
import yaml
import subprocess
import os
import pathlib
import shlex
from typing import overload, TypeVar
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.events import EVENT_TYPE_CREATED, EVENT_TYPE_DELETED, EVENT_TYPE_MOVED
from kirby.cli import CLI
from kirby import __module_dir__

_T = TypeVar('_T')


class Watchdog(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue[FileSystemEvent], loop: asyncio.BaseEventLoop, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue
        self._loop = loop

    def on_any_event(self, event: FileSystemEvent):
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
    
    def cancel(self):
        self._loop.call_soon_threadsafe(self._queue.put_nowait, None)


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


# Tell the YAML dumper how to handle objects of type pathlib.Path
def represent_path(dumper: yaml.SafeDumper, data: pathlib.Path):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))


yaml.SafeDumper.add_representer(pathlib.Path, represent_path)
yaml.SafeDumper.add_representer(pathlib.PosixPath, represent_path)
yaml.SafeDumper.add_representer(pathlib.WindowsPath, represent_path)
yaml.SafeDumper.add_representer(pathlib.PurePath, represent_path)
yaml.SafeDumper.add_representer(pathlib.PurePosixPath, represent_path)
yaml.SafeDumper.add_representer(pathlib.PureWindowsPath, represent_path)


class ItemRandoCaller:
    def __init__(self, cl_args: CLI):
        self.cl_args = cl_args
        system = 'Windows' if platform.system() == 'Windows' else None
        self.config = {
            'vanilla_rom': cl_args.vanilla_rom,
            'speedchoice_rom': cl_args.speedchoice_rom,
            'zxplus_jar': cl_args.upr_zx_jar_path,
            'zxplus_settings': cl_args.upr_zx_settings_path,
            'flips': {system: cl_args.flips_path},
            'item_rando': {system: cl_args.item_rando_path},
        }
        self.settings_file_specs = (
            (self.cl_args.upr_zx_settings_path, '.rnqs'),
            (self.cl_args.item_rando_path.parent / 'Modes', '.yml'),
        )

        # Prepopulate choices
        self.settings_files = {
            parent: set(parent.glob(f'*{ext}'))
            for parent, ext in self.settings_file_specs
        }
        self._path_queue: asyncio.Queue[FileSystemEvent] = asyncio.Queue()

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
        try:
            observer.join()
        finally:
            handler.cancel()

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

    @overload
    async def __call__(
        self,
        *,
        zx_preset: str,
        zx_seed: str | None = None,
        item_preset: str,
        item_seed: str | None = None,
        outfile: os.PathLike
    ) -> asyncio.subprocess.Process: ...

    async def __call__(self, **config) -> asyncio.subprocess.Process:
        config = self.config | config
        config['zx_seed'] = config['zx_seed'] or None
        config['item_seed'] = config['item_seed'] or None
        with tempfile.NamedTemporaryFile(suffix='.yml', mode='w+', delete=False) as conffile:
            yaml.safe_dump(self.config | config, conffile)
        try:
            args = [
                '-c', str(os.cpu_count() or 1),
                '-R', 'create_patchfile',
                '--configfile', conffile.name
            ]
            proc = await asyncio.create_subprocess_exec(
                'snakemake',
                *args,
                cwd=__module_dir__,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if await proc.wait():
                raise subprocess.CalledProcessError(
                    proc.returncode,
                    shlex.join(['snakemake'] + args),
                    (await proc.stdout.read()).decode(),
                    (await proc.stderr.read()).decode(),
                )
        finally:
            os.unlink(conffile.name)
        return proc
