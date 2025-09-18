# cogs/utility.py
# utility commands
# could expand on this more later, if addtional user functionality is wished
import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    # latency command
    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! {latency_ms}ms")
    # information on how to use Rainfall
    @app_commands.command(name="getstarted", description="Detailed instructions for usage of Rainfall")
    async def getstarted(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "DM me to start a ticket with staff! You will be prompted at the beginning if you would like your ticket to be anonymous or for it to have your name attached to it. "
            "You can always elect to reveal who you are to staff later. This bot does not save a log of users who interact with it, and staff cannot forcibly determine who you are if you elect to be anonymous. "
            "Rainfall could be useful for reporting staff misconduct, sexual abuse/misconduct from other server members, or in instances where you are afraid of retaliation or simply are anxious about talking with staff!",
            ephemeral=True
        )

# setup for loading cog
async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))