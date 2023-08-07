import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object

import logging
log = logging.getLogger("Ascension")

from data.models import *

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "scoreboard",
        description = "affiche le scoreboard du serveur"
    )
    async def scoreboard(self, interaction):
        await interaction.response.defer()

        try:
            scoreboards = await Scoreboard.all()
            scoreboard = scoreboards[0]

            users = await scoreboard.users.all()
            for i, runner in enumerate(users):
                personal_best = (await runner.best_times()).total_time
                users[i] = (runner, personal_best)

            users.sort(key = lambda user: user[1])
            digits = len(str(len(users)))

            embed = discord.Embed(
                colour = discord.Colour.blue()
            )

            leaderboard = ""
            for i, (runner, best_time) in enumerate(users):
                old_place = runner.server_rank
                new_place = i + 1
                runner.server_rank = new_place
                await runner.save()

                if new_place < old_place:
                    emote = ":arrow_up_small:"
                elif new_place == old_place:
                    emote = ":black_large_square:"
                else:
                    emote = ":arrow_down_small:"

                leaderboard += (
                    f"{emote} `{str(new_place).rjust(digits)}` | "
                    f":clock1: `{str(best_time)[:-3]}` | "
                    f"<@{runner.user_id}>\n"
                )

            name = "Server Leaderboard"

            embed.add_field(
                inline = False,
                name = name,
                value = leaderboard
            )
        except Exception as e:
            log.exception(e)

        await interaction.followup.send(
            "",
            embed = embed,
        )

async def setup(bot):
    await bot.add_cog(Leaderboard(bot), guilds = [guild_object])
