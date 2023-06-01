import asyncio
import tempfile
import os
import sys
import pathlib
import contextlib
import discord
import traceback
import subprocess
import platform
import yaml
from typing import overload
from discord import app_commands
from discord.ext import commands
from ..discord_bot import DiscordBot
from .. import __module_dir__
from ..util.traceback_limit import traceback_limit


@contextlib.contextmanager
def delete_on_done(pth: str | os.PathLike | pathlib.Path):
    pth = pathlib.Path(pth)
    yield pth
    pth.unlink()


class RandoParamsView(discord.ui.View):
    @discord.ui.select(
        placeholder='Select UPR preset ...',
        min_values=1,
        max_values=1,
    )
    async def monster_preset(self, interaction: discord.Interaction[DiscordBot], cls: discord.ui.Select):
        self.selected_monster_preset = self.bot.cl_args.upr_zx_settings_path / (cls.values[0] + '.rnqs')
        await interaction.response.defer()

    @discord.ui.select(
        placeholder='Select KIR preset ...',
        min_values=1,
        max_values=1,
    )
    async def item_preset(self, interaction: discord.Interaction[DiscordBot], cls: discord.ui.Select):
        self.selected_item_preset = self.bot.cl_args.item_rando_path / 'Modes' / (cls.values[0] + '.yml')
        await interaction.response.defer()
    
    @discord.ui.button(label='Set seeds', emoji='🌱')
    async def seeds_button(self, interaction: discord.Interaction[DiscordBot], button: discord.ui.Button):
        modal = (discord.ui.Modal(title='Enter the randomizer seeds')
            #.add_item(discord.ui.TextInput(label='Pokemon randomizer seed'))
            .add_item(discord.ui.TextInput(label='Item randomizer seed')))
        await interaction.response.send_modal(modal)
        if not await modal.wait():
            #self.monster_seed = str(modal.children[0]) or self.monster_seed
            self.item_seed = str(modal.children[0]) or self.item_seed

    @discord.ui.button(label='Generate!', emoji='🎲')
    async def submit_form(self, interaction: discord.Interaction[DiscordBot], button: discord.ui.Button):
        if not self.monster_preset.values or not self.item_preset.values:
            await interaction.response.send_message(
                'Please select the randomizer presets',
                ephemeral=True
            )
            return
        button.disabled = True
        self.seeds_button.disabled = True
        self.stop()
        await interaction.response.send_message('Generating your ROM ...')
        try:
            with traceback_limit(3):
                outfname = tempfile.mktemp(suffix='.ips')
                try:
                    proc: asyncio.subprocess.Process = await self.cog.randomize_rom(
                        zx_preset=self.monster_preset.values[0],
                        zx_seed=self.monster_seed,
                        item_preset=self.item_preset.values[0],
                        item_seed=self.item_seed,
                        outfile=outfname
                    )
                    stdout, stderr = await proc.communicate()
                    print(stdout.decode())
                    print(stderr.decode(), file=sys.stderr)
                    if proc.returncode == 0:
                        await interaction.edit_original_response(
                            content='Generating your ROM (100%)',
                            embed=discord.Embed()
                                .add_field(
                                    name='Setup',
                                    value='1) Obtain a copy of Pokemon Crystal (U)(1.1) if you haven\'t already\n'
                                        '2) Download and extract [Floating IPS](https://www.smwcentral.net/?p=section&a=details&id=11474) if you haven\'t already',
                                    inline=False
                                ).add_field(
                                    name='Make the ROM',
                                    value='1) Download the patch file below\n'
                                        '2) Launch flips.exe (or flips_linux) and follow the prompts to apply the patch to vanilla crystal',
                                    inline=False
                                ),
                            attachments=[discord.File(outfname, filename=f'{interaction.user.name}_{interaction.id}.ips')]
                        )
                    else:
                        if len(stdout) >= 1000:
                            stdout = stdout[:500] + '...' + stdout[-500:]
                        if len(stderr) >= 1000:
                            stderr = stderr[:500] + '...' + stderr[-500:]
                        await interaction.edit_original_response(
                            content='Building the ROM failed',
                            embed=discord.Embed().add_field(
                                name='stdout', value=f'```{stdout}```', inline=False
                            ).add_field(
                                name='stderr', value=f'```{stderr}```', inline=False
                            )
                        )
                finally:
                    os.unlink(outfname)
        except Exception:
            await interaction.edit_original_response(content=f'Building the ROM failed with reason:\n'
                                                            f'```{traceback.format_exc()}```')
            raise

    def __init__(self, bot: DiscordBot):
        super().__init__()
        self.bot = bot
        self.cog: 'ItemRando' = bot.get_cog('ItemRando')
        self.selected_monster_preset: str = None
        self.selected_item_preset: str = None
        self.monster_seed: str = None
        self.item_seed: str = None
        for config in self.bot.upr_settings_files:
            self.monster_preset.add_option(label=config.stem)
        for preset in self.bot.item_rando_presets:
            self.item_preset.add_option(label=preset.stem)


def represent_path(dumper: yaml.Dumper, data: pathlib.Path):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))


yaml.SafeDumper.add_representer(pathlib.Path, represent_path)
yaml.SafeDumper.add_representer(pathlib.PosixPath, represent_path)
yaml.SafeDumper.add_representer(pathlib.WindowsPath, represent_path)
yaml.SafeDumper.add_representer(pathlib.PurePath, represent_path)
yaml.SafeDumper.add_representer(pathlib.PurePosixPath, represent_path)
yaml.SafeDumper.add_representer(pathlib.PureWindowsPath, represent_path)


class ItemRando(commands.GroupCog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @overload
    async def randomize_rom(self, *, zx_preset: str, zx_seed: str | None = None, item_preset: str, item_seed: str | None = None, outdir: os.PathLike) -> asyncio.subprocess.Process: ...

    async def randomize_rom(self, **config) -> asyncio.subprocess.Process:
        system = platform.system()
        if system != 'Windows':
            system = None  # non-windows uses default key
        config |= {
            'vanilla_rom': self.bot.cl_args.vanilla_rom,
            'speedchoice_rom': self.bot.cl_args.speedchoice_rom,
            'zxplus_jar': self.bot.cl_args.upr_zx_jar_path,
            'zxplus_settings': self.bot.cl_args.upr_zx_settings_path,
            'flips': {system: self.bot.cl_args.flips_path},
            'item_rando': {system: self.bot.cl_args.item_rando_path},
        }
        with tempfile.NamedTemporaryFile(suffix='.yml', mode='w+', delete=False) as conffile:
            yaml.safe_dump(config, conffile)
            conffile.close()
            try:
                proc = await asyncio.create_subprocess_exec(
                    'snakemake', 
                    '-c', '1',
                    '--configfile', conffile.name,
                    cwd=__module_dir__,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                await proc.wait()
            finally:
                os.unlink(conffile.name)
        return proc

    @app_commands.command()
    async def generate(self, interaction: discord.Interaction[DiscordBot]):
        """Generates a patch file to be applied to a vanilla Crystal ROM in order to generate the desired randomization"""
        view = RandoParamsView(self.bot)
        await interaction.response.send_message(view=view, ephemeral=True)
    
    async def cog_app_command_error(self, interaction: discord.Interaction[DiscordBot], error: discord.app_commands.AppCommandError):
        error = getattr(error, 'original', error)
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title='Error',
            description=f'```{"".join(traceback.format_exception(error.__class__, error, error.__traceback__))}```'
        )
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: DiscordBot):
    await bot.add_cog(ItemRando(bot))
