import discord
import asyncio
from discord.ext import commands
from .discord_bot import DiscordBot
from .cli import CLI

args = CLI()
bot = DiscordBot(args, commands.when_mentioned_or(args.command_prefix), intents=discord.Intents.default())


@commands.is_owner()
@bot.command()
async def sync(ctx: commands.Context[DiscordBot]):
    await asyncio.gather(bot.tree.sync(), *(bot.tree.sync(guild=guild) for guild in bot.guilds))
    await ctx.reply('App commands have been updated in all guilds', ephemeral=True)


@commands.is_owner()
@bot.command()
async def reload(ctx: commands.Context[DiscordBot], extension: str):
    await bot.reload_extension(extension)
    await ctx.reply(f'Reloaded extension {extension}', ephemeral=True)


bot.run(args.token)
