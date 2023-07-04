import discord
import asyncio
from discord.ext import commands
from kirby.discord_bot import DiscordBot
from kirby.cli import CLI
from kirby.web.server import make_app


async def main():
    args = CLI()
    bot = DiscordBot(args, commands.when_mentioned_or(args.command_prefix), intents=discord.Intents.default())
    app = make_app(args)
    await asyncio.gather(
        bot.start(args.token),
        app.run_task(args.webapp_host, args.webapp_port, shutdown_trigger=bot.closed.wait, debug=True)
    )


asyncio.run(main())
