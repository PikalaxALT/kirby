import discord
from discord.ext import commands
from .discord_bot import DiscordBot
from .cli import CLI

args = CLI()
bot = DiscordBot(commands.when_mentioned_or(args.command_prefix), intents=discord.Intents.default())
bot.run(args.token)
