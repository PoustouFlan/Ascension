import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object

import logging
log = logging.getLogger("Ascension")

from data.models import *

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "register",
        description = "Adds a new user to the scoreboard"
    )
    async def register(self, interaction, user:discord.Member):
        runner = await Runner.get_existing_or_create(user.id)

        scoreboards = await Scoreboard.all()
        scoreboard = scoreboards[0]

        added = await scoreboard.add_user_if_not_present(runner)

        if added:
            await interaction.response.send_message(
                f"User added in the scoreboard"
            )
        else:
            await interaction.response.send_message(
                f"User is already present in the scoreboard"
            )

async def setup(bot):
    await bot.add_cog(Register(bot), guilds = [guild_object])
