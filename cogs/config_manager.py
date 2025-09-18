# cogs/config_manager.py
# manages configuration related tasks
import os
import json
import discord
from discord.ext import commands
from discord import app_commands

# Directory where configs are stored
CONFIG_DIR = "guild_configs"

# Resolve cogs directory relative to this file (robust to working directory)
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
COGS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "cogs")

# Ensure config directory exists
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)


class ConfigManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # config helpers
    def get_guild_config_path(self, guild: discord.Guild) -> str:
        guild_folder = os.path.join(CONFIG_DIR, str(guild.id))
        os.makedirs(guild_folder, exist_ok=True)
        return os.path.join(guild_folder, "config.json")

    def load_config(self, guild: discord.Guild) -> dict:
        path = self.get_guild_config_path(guild)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def save_config(self, guild: discord.Guild, data: dict):
        path = self.get_guild_config_path(guild)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    # permission helpers
    async def is_admin(self, user: discord.User, guild: discord.Guild) -> bool:
        config = self.load_config(guild)
        admin_list = config.get("rainfall_admins", [])
        return user.id in admin_list or await self.bot.is_owner(user)

    async def is_staff(self, user: discord.User, guild: discord.Guild) -> bool:
        config = self.load_config(guild)
        admin_list = config.get("rainfall_admins", [])
        staff_list = config.get("rainfall_staff", [])
        return (
            user.id in staff_list
            or user.id in admin_list
            or await self.bot.is_owner(user)
        )

    # configuration slash commands
    # set channel where threads will be created
    @app_commands.command(name="set_thread_channel", description="Set the Rainfall thread channel for this guild.")
    async def set_thread_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                "Only Rainfall Admins or the bot owner can run this.",
                ephemeral=True
            )
            return

        config = self.load_config(interaction.guild)
        config["rainfall_thread_channel"] = channel.id
        self.save_config(interaction.guild, config)
        await interaction.response.send_message(
            f"Rainfall thread channel set to {channel.mention} (ID: {channel.id})",
            ephemeral=True
        )
    # add a user to admins list 
    @app_commands.command(name="add_admin", description="Add a user to the Rainfall Admins list.")
    async def add_admin(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
            return

        config = self.load_config(interaction.guild)
        admin_list = config.get("rainfall_admins", [])
        if member.id not in admin_list:
            admin_list.append(member.id)
            config["rainfall_admins"] = admin_list
            self.save_config(interaction.guild, config)
            await interaction.response.send_message(f"Added {member.display_name} to Rainfall Admins.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.display_name} is already in Rainfall Admins.", ephemeral=True)
    # remove user from admins list
    @app_commands.command(name="remove_admin", description="Remove a user from the Rainfall Admins list.")
    async def remove_admin(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
            return

        config = self.load_config(interaction.guild)
        admin_list = config.get("rainfall_admins", [])
        if member.id in admin_list:
            admin_list.remove(member.id)
            config["rainfall_admins"] = admin_list
            self.save_config(interaction.guild, config)
            await interaction.response.send_message(f"Removed {member.display_name} from Rainfall Admins.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.display_name} is not in Rainfall Admins.", ephemeral=True)
    # add user to staff list
    @app_commands.command(name="add_staff", description="Add a staff member to the Rainfall Staff list.")
    async def add_staff(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message("Only Rainfall Admins or the bot owner can run this.", ephemeral=True)
            return

        config = self.load_config(interaction.guild)
        staff_list = config.get("rainfall_staff", [])
        if member.id not in staff_list:
            staff_list.append(member.id)
            config["rainfall_staff"] = staff_list
            self.save_config(interaction.guild, config)
            await interaction.response.send_message(f"Added {member.display_name} to Rainfall Staff.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.display_name} is already in Rainfall Staff.", ephemeral=True)
    # remove user from staff list
    @app_commands.command(name="remove_staff", description="Remove a staff member from the Rainfall Staff list.")
    async def remove_staff(self, interaction: discord.Interaction, member: discord.Member):
        if not await self.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message("Only Rainfall Admins or the bot owner can run this.", ephemeral=True)
            return

        config = self.load_config(interaction.guild)
        staff_list = config.get("rainfall_staff", [])
        if member.id in staff_list:
            staff_list.remove(member.id)
            config["rainfall_staff"] = staff_list
            self.save_config(interaction.guild, config)
            await interaction.response.send_message(f"Removed {member.display_name} from Rainfall Staff.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.display_name} is not in Rainfall Staff.", ephemeral=True)
    # view server-specific config file
    @app_commands.command(name="view_config", description="View this guild's Rainfall config.")
    async def view_config(self, interaction: discord.Interaction):
        if not await self.is_staff(interaction.user, interaction.guild):
            await interaction.response.send_message("Only Rainfall Staff, Admins, or the bot owner can run this.", ephemeral=True)
            return

        config = self.load_config(interaction.guild)
        if not config:
            await interaction.response.send_message("No config set for this guild yet.", ephemeral=True)
        else:
            formatted = json.dumps(config, indent=4)
            await interaction.response.send_message(f"```json\n{formatted}\n```", ephemeral=True)
    # list all staff present in the server-specific config file
    @app_commands.command(name="list_staff", description="List all Rainfall Admins and Staff in this guild.")
    async def list_staff(self, interaction: discord.Interaction):
        if not await self.is_staff(interaction.user, interaction.guild):
            await interaction.response.send_message("Only Rainfall Staff, Admins, or the bot owner can run this.", ephemeral=True)
            return

        config = self.load_config(interaction.guild)
        admin_list = config.get("rainfall_admins", [])
        staff_list = config.get("rainfall_staff", [])

        def resolve_name(uid: int) -> str:
            member = interaction.guild.get_member(uid)
            return member.display_name if member else f"Unknown User ({uid})"

        admins_str = "\n".join(resolve_name(uid) for uid in admin_list) if admin_list else "None set"
        staff_str = "\n".join(resolve_name(uid) for uid in staff_list) if staff_list else "None set"

        msg = f"**Rainfall Admins**:\n{admins_str}\n\n**Rainfall Staff**:\n{staff_str}"
        await interaction.response.send_message(msg, ephemeral=True)

# setup for loading cog
async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigManager(bot))
