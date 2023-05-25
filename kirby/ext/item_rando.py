import bsdiff4
import asyncio
import tempfile
import os
import pathlib
import contextlib
import discord
import subprocess
import shlex
from discord import app_commands
from discord.ext import commands
from ..discord_bot import DiscordBot


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
        self.stop()
        await interaction.response.send_message('Generating your ROM (0%)...')
        try:
            with contextlib.ExitStack() as stack:
                # Step 1: Invoke the UPR to generate the monster rando from Crystal Speedchoice
                monster_patched_rom = stack.enter_context(delete_on_done(
                    await self.invoke_upr_zx(
                        self.selected_monster_preset,
                        self.monster_seed
                    )
                ))
                await interaction.response.edit_message(content='Generating your ROM (33%)...')
                # Step 2: Invoke the Item Rando on the ROM from step 1 to generate the item-randomized ROM
                item_patched_rom = stack.enter_context(delete_on_done(
                    await self.invoke_item_rando(
                        monster_patched_rom,
                        self.selected_item_preset,
                        self.item_seed
                    )
                ))
                await interaction.response.edit_message(content='Generating your ROM (66%)...')
                # Step 3: Compute the diff between the step 2 ROM and vanilla Crystal
                patch_file = stack.enter_context(delete_on_done(
                    self.generate_patch(
                        self.bot.cl_args.vanilla_rom,
                        item_patched_rom
                    )
                ))
                # Step 4: Upload the patch
                await interaction.response.edit_message(
                    content='Generating your ROM (100%)\n\n',
                    embed=discord.Embed()
                        .add_field(
                            name='Setup',
                            value='1) Obtain a copy of Pokemon Crystal (U)(1.1) if you haven\'t already\n'
                                '2) Download and install bspatch.exe from [here](https://github.com/cnSchwarzer/bsdiff-win/releases/tag/latest) if you haven\'t already'
                        ).add_field(
                            name='Make the ROM',
                            value='1) Download the patch file below\n'
                                '2) In a Command Prompt or PowerShell window, run: `path\\to\\bspatch.exe path\\to\\crystal.gbc path\\to\\output.gbc path\\to\\patch.bsdiff4`', 
                        ),
                    attachments=[discord.File(patch_file, filename=f'{interaction.user.name}_{interaction.id}.bsdiff4')]
                )
        except subprocess.CalledProcessError as e:
            await interaction.response.edit_message(content=f'ERROR: Command `{e.cmd}` failed with return code {e.returncode}\n'
                                                            f'stdout: ```{e.stdout.decode()}```\n'
                                                            f'stderr: ```{e.stderr.decode()}```')
    
    async def call_randomizer(self, *command: str):
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        returncode = await process.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, shlex.join(command), *(await process.communicate()))

    async def invoke_upr_zx(self, preset: pathlib.Path, seed: str) -> pathlib.Path:
        randomized_rom = tempfile.mkstemp(suffix='.gbc')
        await self.call_randomizer(
            'java', '-jar', '-Xmmx', '768M', self.bot.cl_args.upr_zx_jar_path,
            '-i', self.bot.cl_args.speedchoice_rom,
            '-o', randomized_rom,
            '-s', preset
        )
        return randomized_rom
    
    async def invoke_item_rando(self, baserom: pathlib.Path, preset: pathlib.Path, seed: str) -> pathlib.Path:
        randomized_rom = tempfile.mkstemp(suffix='.gbc')
        await self.call_randomizer(
            self.bot.cl_args.item_rando_path / 'Pokemon Crystal Item Randomizer', 'cli',
            '-i', baserom,
            '-o', randomized_rom,
            '-m', preset.relative_to(self.bot.cl_args.item_rando_path),
            '-s', seed
        )
        return randomized_rom
    
    @staticmethod
    def generate_patch(baserom: pathlib.Path, modified_rom: pathlib.Path) -> pathlib.Path:
        patchfile = tempfile.mkstemp(suffix='.bsdiff4')
        bsdiff4.file_diff(baserom, modified_rom, patchfile)
        return pathlib.Path(patchfile)

    def __init__(self, bot: DiscordBot):
        super().__init__(title='Select randomizer presets')
        self.bot = bot
        self.selected_monster_preset: str = None
        self.selected_item_preset: str = None
        self.monster_seed: str = None
        self.item_seed: str = None
        for config in self.bot.upr_settings_files:
            self.monster_preset.add_option(label=config.stem)
        for preset in self.bot.item_rando_presets:
            self.item_preset.add_option(label=preset.stem)


class ItemRando(commands.GroupCog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot
    
    @app_commands.command()
    async def generate(self, interaction: discord.Interaction[DiscordBot]):
        """Generates a patch file to be applied to a vanilla Crystal ROM in order to generate the desired randomization"""
        view = RandoParamsView(self.bot)
        await interaction.response.send_message(view=view, ephemeral=True)


async def setup(bot: DiscordBot):
    await bot.add_cog(ItemRando(bot))
