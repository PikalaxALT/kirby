import discord
import asyncio
from discord.ext import commands
from kirby.discord_bot import DiscordBot
from kirby.cli import CLI
from kirby.web.server import make_app
from kirby.util.item_rando_caller import ItemRandoCaller


async def main():
    args = CLI()
    rando = ItemRandoCaller(args)
    intents = discord.Intents.default()
    intents.message_content = True
    bot = DiscordBot(args, rando, commands.when_mentioned_or(args.command_prefix), intents=intents)
    app = make_app(args, rando)
    debug_webapp = args.webapp_host in {'localhost', '127.0.0.1'}
    await asyncio.gather(
        rando.sync_presets(),
        bot.start(args.token),
        app.run_task(args.webapp_host, args.webapp_port, shutdown_trigger=bot.closed.wait, debug=debug_webapp)
    )


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
