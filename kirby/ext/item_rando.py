import asyncio
import tempfile
import os
import pathlib
import contextlib
import discord
import traceback
import snakemake
from typing import overload
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
        await interaction.response.send_message('Generating your ROM ...')
        try:
            with tempfile.NamedTemporaryFile(suffix='.ips') as outfile:
                if await self.cog.randomize_rom(
                    zx_preset=self.monster_preset,
                    zx_seed=self.monster_seed,
                    item_preset=self.item_preset,
                    item_seed=self.item_seed,
                    outfile=outfile.name
                ):
                    await interaction.response.edit_message(
                        content='Generating your ROM (100%)\n\n',
                        embed=discord.Embed()
                            .add_field(
                                name='Setup',
                                value='1) Obtain a copy of Pokemon Crystal (U)(1.1) if you haven\'t already\n'
                                      '2) Download and extract [Floating IPS](https://www.smwcentral.net/?p=section&a=details&id=11474) if you haven\'t already'
                            ).add_field(
                                name='Make the ROM',
                                value='1) Download the patch file below\n'
                                      '2) Launch flips.exe (or flips_linux) and follow the prompts to apply the patch to vanilla crystal', 
                            ),
                        attachments=[discord.File(outfile, filename=f'{interaction.user.name}_{interaction.id}.ips')]
                    )
                else:
                    await interaction.response.edit_message(content='Building the ROM failed but no reason was given')
        except Exception:
            await interaction.response.edit_message(content=f'Building the ROM failed with reason:\n'
                                                            f'```{traceback.format_exc()}```')
            raise

    def __init__(self, bot: DiscordBot):
        super().__init__(title='Select randomizer presets')
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


class ItemRando(commands.GroupCog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @overload
    async def randomize_rom(self, *, zx_preset: str, zx_seed: str | None = None, item_preset: str, item_seed: str | None = None, outdir: os.PathLike): ...

    async def randomize_rom(self, **config):
        return await asyncio.to_thread(
            snakemake.snakemake, self.bot.package_dir / 'Snakefile', config=config
        )

    @app_commands.command()
    async def generate(self, interaction: discord.Interaction[DiscordBot]):
        """Generates a patch file to be applied to a vanilla Crystal ROM in order to generate the desired randomization"""
        view = RandoParamsView(self.bot)
        await interaction.response.send_message(view=view, ephemeral=True)


async def setup(bot: DiscordBot):
    await bot.add_cog(ItemRando(bot))
