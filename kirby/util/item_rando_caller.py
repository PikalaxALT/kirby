import asyncio
import platform
import tempfile
import yaml
import subprocess
import os
import pathlib
import shlex
from typing import overload
from kirby.cli import CLI
from kirby import __module_dir__


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
