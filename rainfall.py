# rainfall.py
# main python file, loads cogs in rainfall/cogs/
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import sys
import asyncio
import traceback

# Load .env file
load_dotenv()
TOKEN = os.getenv("RAINFALLTOKEN")
if not TOKEN:
    print("ERROR: RAINFALLTOKEN not found in environment. Set it in your .env or environment variables.")
    sys.exit(1)

# Set config directory
CONFIG_DIR = "guild_configs"

# Store cog: error message for failed loads
FAILED_COGS = {}

# Set directory info for cogs
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))  # directory of rainfall.py
COGS_DIR = os.path.join(SCRIPT_DIR, "cogs")  # directory of cogs relative to rainfall.py

# NOTE: ensure rainfall/cogs is a Python package (contains __init__.py) so load_extension("cogs.xxx") works.

# Discord intents (check dev portal to make sure all are enabled)
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.dm_messages = True
intents.guild_messages = True

description = '''I help users get in contact with staff members! Shoot me a DM to get started! If you do not feel comfortable identifying yourself
to staffers, you may elect to anonymously send messages. Maintained by Sadie [@StylisticallyCatgirl].'''

bot = commands.Bot(command_prefix='r;', description=description, intents=intents)


# Initialization
@bot.event
async def on_ready():
    try:
        # Sync slash commands globally
        global_commands = await bot.tree.sync()
        print(f"Synced {len(global_commands)} commands globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Let's chat!"))


# Load cogs
async def load_cogs():
    if not os.path.exists(COGS_DIR):
        print(f"Cogs directory not found: {COGS_DIR}")
        sys.exit(1)  # exit if cogs can't be loaded

    for filename in os.listdir(COGS_DIR):
        if filename.endswith(".py"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                print(f"Loaded {extension}")
            except Exception as e:
                FAILED_COGS[extension] = str(e)
                print(f"Failed to load {extension}: {e}")


# ─── Global Error Handlers ───

# print errors to terminal
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"[App Command Error] in /{interaction.command.name if interaction.command else 'unknown'}:")
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    # Notify user
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "An error occurred while running this command.",
                ephemeral=True
            )
    except Exception:
        # Interaction may already be acknowledged or otherwise problematic; swallow to avoid crashing
        pass


# handle errors w/ prefix (somewhat redundant due to lack of prefixed commands)
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    print(f"[Command Error] in command {ctx.command}:")
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


# Unhandled errors in listeners
@bot.event
async def on_error(event_method: str, *args, **kwargs):
    print(f"[Unhandled Error] in event {event_method}:")
    traceback.print_exc()


# Cog management, limited to Sadie
# reload specific cog
@bot.tree.command(name="reload_cog", description="Reload a bot Cog.")
async def reload_cog(interaction: discord.Interaction, cog: str):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
        return
    try:
        await bot.unload_extension(cog)
        await bot.load_extension(cog)
        FAILED_COGS.pop(cog, None)
        await interaction.response.send_message(f"Reloaded `{cog}` successfully!", ephemeral=True)
    except Exception as e:
        FAILED_COGS[cog] = str(e)
        await interaction.response.send_message(f"Failed to reload `{cog}`: `{e}`", ephemeral=True)


# load specific cog
@bot.tree.command(name="load_cog", description="Load a bot Cog.")
async def load_cog(interaction: discord.Interaction, cog: str):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
        return
    try:
        await bot.load_extension(cog)
        FAILED_COGS.pop(cog, None)
        await interaction.response.send_message(f"Loaded `{cog}` successfully!", ephemeral=True)
    except Exception as e:
        FAILED_COGS[cog] = str(e)
        await interaction.response.send_message(f"Failed to load `{cog}`: `{e}`", ephemeral=True)


# unload specific cog
@bot.tree.command(name="unload_cog", description="Unload a bot Cog.")
async def unload_cog(interaction: discord.Interaction, cog: str):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
        return
    try:
        await bot.unload_extension(cog)
        await interaction.response.send_message(f"Unloaded `{cog}` successfully!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Failed to unload `{cog}`: `{e}`", ephemeral=True)


# list all loaded cogs
@bot.tree.command(name="list_cogs", description="List all loaded and failed cogs.")
async def list_cogs(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
        return

    loaded = list(bot.extensions.keys())
    msg = ""

    if loaded:
        msg += "**Loaded cogs:**\n" + "\n".join(f"- `{c}`" for c in loaded)
    else:
        msg += "No cogs are currently loaded."

    if FAILED_COGS:
        msg += "\n\n**Failed cogs:**\n"
        msg += "\n".join(f"- `{c}` → `{err}`" for c, err in FAILED_COGS.items())

    await interaction.response.send_message(msg, ephemeral=True)


# load all cogs from /rainfall/cogs/
@bot.tree.command(name="load_all_cogs", description="Load all cogs from the /rainfall/cogs/ folder.")
async def load_all_cogs(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
        return

    if not os.path.exists(COGS_DIR):
        await interaction.response.send_message(f"Cogs directory not found: `{COGS_DIR}`", ephemeral=True)
        return

    loaded, failed = [], []
    for filename in os.listdir(COGS_DIR):
        if filename.endswith(".py"):
            ext = f"cogs.{filename[:-3]}"
            if ext in bot.extensions:
                continue
            try:
                await bot.load_extension(ext)
                loaded.append(ext)
            except Exception as e:
                failed.append(f"{ext}: {e}")

    msg = ""
    if loaded:
        msg += "**Loaded cogs:**\n" + "\n".join(f"- `{c}`" for c in loaded)
    if failed:
        msg += "\n\n**❌ Failed to load:**\n" + "\n".join(f"- {f}" for f in failed)
    if not loaded and not failed:
        msg = "⚠️ No new cogs to load."

    await interaction.response.send_message(msg, ephemeral=True)


# reload all cogs from /rainfall/cogs/
@bot.tree.command(name="reload_all_cogs", description="Reload all cogs in the /rainfall/cogs/ folder.")
async def reload_all_cogs(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You don't look like Sadie...", ephemeral=True)
        return

    if not os.path.exists(COGS_DIR):
        await interaction.response.send_message(f"Cogs directory not found: `{COGS_DIR}`", ephemeral=True)
        return

    reloaded, failed = [], []
    for filename in os.listdir(COGS_DIR):
        if filename.endswith(".py"):
            ext = f"cogs.{filename[:-3]}"
            try:
                if ext in bot.extensions:
                    await bot.unload_extension(ext)
                await bot.load_extension(ext)
                reloaded.append(ext)
            except Exception as e:
                failed.append(f"{ext}: {e}")

    msg = ""
    if reloaded:
        msg += "**Reloaded cogs:**\n" + "\n".join(f"- `{c}`" for c in reloaded)
    if failed:
        msg += "\n\n**Failed to reload:**\n" + "\n".join(f"- {f}" for f in failed)
    if not reloaded and not failed:
        msg = "No cogs were reloaded."

    await interaction.response.send_message(msg, ephemeral=True)


# run bot with loaded cogs
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())