import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import *

import logging
log = logging.getLogger("Ascension")

from data.models import *

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def embed_runner(runner):
        embed = discord.Embed(
            title = "Runner profile",
            colour = discord.Colour.orange()
        )
        best_run = await runner.best_times()
        embed.add_field(
            name = "Personal Bests",
            inline = False,
            value = best_run.description()
        )
        # ...
        return embed

    @app_commands.command(
        name = "user-info",
        description = "Displays description of a runner"
    )
    async def user_info(self, interaction, user:discord.Member):
        await interaction.response.defer()

        runner = await Runner.get_existing_or_create(user.id)
        embed = await UserInfo.embed_runner(runner)

        await interaction.followup.send(
            "",
            embed = embed
        )



async def setup(bot):
    await bot.add_cog(UserInfo(bot), guilds = [guild_object])
