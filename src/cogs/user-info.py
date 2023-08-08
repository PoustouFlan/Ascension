import discord
from discord.ext import commands
from discord import app_commands
from bot_utils import *

import logging
log = logging.getLogger("Ascension")

from data.models import *

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from datetime import timedelta


class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def plot_formatter(x, pos):
        time = timedelta(seconds = x)
        return str(time)[:-3]

    @staticmethod
    async def plot_runner(runner, filename):
        formatter = FuncFormatter(UserInfo.plot_formatter)

        dates = []
        times = []
        async for run in runner.runs.all():
            if run.date is None:
                continue
            dates.append(run.date)
            times.append(run.total_time.seconds)

        plt.grid(which='major', axis='y', color='gray', linestyle='dashed', linewidth=0.5, alpha=0.5)
        plt.plot(dates, times, color='gold')
        plt.xticks(color='white')
        plt.yticks(color='white')
        plt.gca().spines['bottom'].set_color('white')
        plt.gca().spines['left'].set_color('white')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.xticks(rotation=45)
        plt.tick_params(axis='x',colors='white')
        plt.tick_params(axis='y',colors='white')
        plt.tight_layout()
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.savefig(filename, dpi=300, transparent=True)
        plt.close()


    async def embed_runner(self, runner):
        guild = await self.bot.fetch_guild(GUILD_ID)
        member = await guild.fetch_member(runner.user_id)

        embed = discord.Embed(
            title = f"{member.nick}'s profile",
            colour = discord.Colour.orange()
        )
        avatar = member.guild_avatar
        if avatar is None:
            avatar = member.avatar
        embed.set_thumbnail(url=avatar.url)

        best_run = await runner.best_times()
        sobs_time = timedelta()
        sobs_death = 0
        for chapter in range(1, 8):
            sobs_time += getattr(best_run, f'chapter{chapter}_time')
            sobs_death += getattr(best_run, f'chapter{chapter}_death')

        fd = lambda d: str(d).rjust(3)
        ft = lambda t: str(t)[:-3]
        description = best_run.description()
        description += f"`SOBS            `:skull:`{fd(sobs_death)   }` | :clock1: `{ft(sobs_time)   }`\n"
        embed.add_field(
            name = "Personal Bests",
            inline = False,
            value = description
        )

        value = ''
        all_runs = await runner.runs.all()
        for run in all_runs[-5:][::-1]:
            pb = (run.total_time == best_run.total_time)
            time = str(run.total_time)[:-3]
            date = run.date.strftime('%d/%m/%y %H:%M:%S')
            if pb:
                value += f"`{date}` | `{time}` :star:\n"
            else:
                value += f"`{date}` | `{time}`\n"
        embed.add_field(
            name = "Last Runs",
            inline = False,
            value = value
        )

        filename = f'data/tmp/{runner.user_id}_plot.png'
        await UserInfo.plot_runner(runner, filename)
        file = discord.File(filename, filename = filename[9:])
        embed.set_image(url = f"attachment://{filename[9:]}")

        return embed, file

    @app_commands.command(
        name = "user-info",
        description = "Displays description of a runner"
    )
    async def user_info(self, interaction, user:discord.Member):
        await interaction.response.defer()

        runner = await Runner.get_existing_or_create(user.id)
        embed, file = await self.embed_runner(runner)

        await interaction.followup.send(
            "",
            embed = embed,
            file = file
        )


async def setup(bot):
    await bot.add_cog(UserInfo(bot), guilds = [guild_object])
