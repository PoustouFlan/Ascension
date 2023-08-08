import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object

import logging
log = logging.getLogger("Ascension")

from data.models import *

class Edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "edit",
        description = "Edit a run"
    )
    async def edit(self, interaction, run_id:str, field:str, value:str):
        run = await CelesteRun.get_existing(run_id)
        if run is None:
            await interaction.response.send_message("Run does not exist. Check id.")
            return

        if not hasattr(run, field):
            await interaction.response.send_message("Field does not exist.")
            return

        if field.endswith('time'):
            regex = '(\d+:)?(\d+):(\d+).(\d+)'
            match = re.match(regex, value)
            if match is None:
                await interaction.response.send_message("Value is not a properly formatted time")
                return
            hours, minutes, seconds, milliseconds = match.group(1, 2, 3, 4)
            if hours is None:
                hours = 0
            else:
                hours = hours[:-1]

            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)
            milliseconds = int(milliseconds)

            value = timedelta(
                hours = hours,
                minutes = minutes,
                seconds = seconds,
                milliseconds = milliseconds
            )
        elif field.endswith('death'):
            try:
                value = int(value)
            except ValueError:
                await interaction.response.send_message("Value should be an integer")
                return
        else:
            await interaction.response.send_message("This field is not editable")
            return

        setattr(run, field, value)
        await run.save()

        await interaction.response.send_message("Run successfully edited")


async def setup(bot):
    await bot.add_cog(Edit(bot), guilds = [guild_object])
