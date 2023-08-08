import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import guild_object, GUILD_ID

import logging
log = logging.getLogger("Ascension")

from data.models import *

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from datetime import timedelta

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def plot_formatter(x, pos):
        time = timedelta(seconds = x)
        return str(time)[:-3]

    async def plot_runners(self, runners, filename, field):
        formatter = FuncFormatter(Leaderboard.plot_formatter)
        guild = await self.bot.fetch_guild(GUILD_ID)

        for runner in runners:
            member = await guild.fetch_member(runner.user_id)
            dates = []
            values = []
            async for run in runner.runs.all():
                if run.date is None:
                    continue
                dates.append(run.date)
                value = getattr(run, field)
                if field.endswith('time'):
                    value = value.seconds
                values.append(value)
            plt.plot(dates, values, label = member.nick)

        plt.grid(which='major', axis='y', color='gray', linestyle='dashed', linewidth=0.5, alpha=0.5)
        plt.xticks(color='white')
        plt.yticks(color='white')
        plt.gca().spines['bottom'].set_color('white')
        plt.gca().spines['left'].set_color('white')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.xticks(rotation=45)
        plt.tick_params(axis='x',colors='white')
        plt.tick_params(axis='y',colors='white')
        plt.legend(loc=(1.05, 0.25))
        plt.tight_layout()
        if field.endswith('time'):
            plt.gca().yaxis.set_major_formatter(formatter)

        plt.savefig(filename, dpi=300, transparent=True)
        plt.close()

    @app_commands.command(
        name = "scoreboard",
        description = "affiche le scoreboard du serveur"
    )
    async def scoreboard(self, interaction, field:str='total_time'):
        await interaction.response.defer()

        scoreboards = await Scoreboard.all()
        scoreboard = scoreboards[0]

        runners = await scoreboard.users.all()
        users = []
        for runner in runners:
            personal_best = await runner.best_times()
            if not hasattr(personal_best, field):
                await interaction.followup.send("Invalid field.")
                return
            value = getattr(personal_best, field)
            users.append((runner, value))

        users.sort(key = lambda user: user[1])
        digits = len(str(len(users)))

        embed = discord.Embed(
            colour = discord.Colour.blue()
        )

        leaderboard = ""
        for i, (runner, value) in enumerate(users):
            if field.endswith('time'):
                value = str(value)[:-3]
            if field == 'total_time':
                old_place = runner.server_rank
                new_place = i + 1
                runner.server_rank = new_place
                await runner.save()
            else:
                new_place = old_place = i+1

            if new_place < old_place:
                emote = ":arrow_up_small:"
            elif new_place == old_place:
                emote = ":black_large_square:"
            else:
                emote = ":arrow_down_small:"

            leaderboard += (
                f"{emote} `{str(new_place).rjust(digits)}` | "
                f":clock1: `{value}` | "
                f"<@{runner.user_id}>\n"
            )

        name = f"Server Leaderboard ({field})"
        embed.add_field(
            inline = False,
            name = name,
            value = leaderboard
        )

        try:
            filename = f'data/tmp/scoreboard_plot.png'
            await self.plot_runners(runners, filename, field)
            file = discord.File(filename, filename = filename[9:])
            embed.set_image(url = f"attachment://{filename[9:]}")
        except Exception as e:
            log.exception(e)

        await interaction.followup.send(
            "",
            embed = embed,
            file = file,
        )

async def setup(bot):
    await bot.add_cog(Leaderboard(bot), guilds = [guild_object])
