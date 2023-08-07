import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object

import logging
log = logging.getLogger("Ascension")

from data.models import *

from datetime import datetime

class AddRun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name = 'add-run-context',
            callback = self.add_run_context
        )
        self.bot.tree.add_command(self.ctx_menu, guild=guild_object)

    @staticmethod
    def embed_run(run):
        embed = discord.Embed(
            title = "New run",
            colour = discord.Colour.orange()
        )

        embed.add_field(
            name = '',
            inline = False,
            value = (
                f"ID:   `{run.id}`\n"
                f"Date: `{run.date}`\n"
            )
        )

        embed.add_field(
            name = '',
            inline = False,
            value = run.description()
        )

        return embed

    @staticmethod
    async def load_screenshot(
        screenshot: discord.Attachment,
        date: datetime,
        user_id: int
    ):
        await screenshot.save("data/tmp/screenshot.png")
        run = await CelesteRun.from_image("data/tmp/screenshot.png", date = date)

        runner = await Runner.get_existing_or_create(user_id)
        await runner.add_run(run)
        embed = AddRun.embed_run(run)

        return embed

    async def add_run_context(
        self, interaction,
        message: discord.Message,
    ):
        await interaction.response.defer()

        user_id = message.author.id
        screenshot = message.attachments[0] # /!\
        embed = await AddRun.load_screenshot(
            screenshot, message.created_at, user_id
        )

        await interaction.followup.send(
            "",
            embed = embed
        )

    @app_commands.command(
        name = "add-run",
        description = "register a run from a screenshot"
    )
    async def add_run(
        self, interaction,
        screenshot: discord.Attachment,
        date: str = "",
        user: discord.Member = None
    ):
        await interaction.response.defer()

        if date == '':
            date = datetime.now()
        else:
            if ':' in date:
                date = datetime.strptime(date, '%d/%m/%y %H:%M:%S')
            else:
                date = datetime.strptime(date, '%d/%m/%y')

        if user is None:
            user_id = interaction.user.id
        else:
            user_id = user.id

        embed = await AddRun.load_screenshot(screenshot, date, user_id)

        await interaction.followup.send(
            "",
            embed = embed
        )

async def setup(bot):
    await bot.add_cog(AddRun(bot), guilds = [guild_object])
