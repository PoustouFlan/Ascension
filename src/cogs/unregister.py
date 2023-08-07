import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object

import logging
log = logging.getLogger("Ascension")

from data.models import *

class Unregister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "unregister",
        description = "Removes a user from the scoreboard"
    )
    async def unregister(self, interaction, user:discord.Member):

        runner = await Runner.get_existing_or_create(user.id)

        scoreboards = await Scoreboard.all()
        scoreboard = scoreboards[0]

        removed = await scoreboard.remove_user_if_present(runner)

        if removed:
            await interaction.response.send_message(
                f"User removed from the scoreboard"
            )
        else:
            await interaction.response.send_message(
                f"User absent from the scoreboard"
            )

async def setup(bot):
    await bot.add_cog(Unregister(bot), guilds = [guild_object])
