import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object

import logging
log = logging.getLogger("Ascension")

from data.models import *

class Delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "delete",
        description = "Delete a run"
    )
    async def delete(self, interaction, run_id:str):
        run = await CelesteRun.get_existing(run_id)
        if run is None:
            await interaction.response.send_message("Run does not exist. Check id.")
            return

        await run.delete()

        await interaction.response.send_message("Run successfully deleted")


async def setup(bot):
    await bot.add_cog(Delete(bot), guilds = [guild_object])
