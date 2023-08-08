import discord
import asyncio
from bot_utils import *
from discord.ext import commands

import logging
log = logging.getLogger("Ascension")
log.setLevel(logging.DEBUG)
stream = logging.StreamHandler()
log.addHandler(stream)

from data.db_init import init
from data.models import *

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix = "$ ",
    help_command = None,
    intents = intents
)

initial_extensions = [
    "cogs.register",
    "cogs.unregister",
    "cogs.add_run",
    "cogs.user-info",
    "cogs.scoreboard",
    "cogs.edit",
]

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user}")

@bot.command()
async def yolosync(ctx):
    log.info("Synchronization start")
    try:
        commands = await bot.tree.sync(guild = guild_object)
        log.info("Synchronization complete!")
        log.info(f"{len(commands)} command(s) synchronized")
        for cmd in commands:
            print(" -", cmd.name)
    except Exception as e:
        log.exception(str(e))

async def load():
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            log.info(f"{extension} loaded successfully!")
        except Exception as e:
            log.info(f"{extension} failed to load!")
            log.error(e)


async def main():
    await init()
    await load()

    await bot.start(TOKEN)

asyncio.run(main())
