from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import asyncio
import os
import sys
import traceback

# ---------------------------
# Keep-alive server (runs once)
# ---------------------------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ---------------------------
# Load environment variables safely
# ---------------------------
def get_env_var(name, cast=str):
    value = os.environ.get(name)
    if value is None:
        print(f"❌ Missing environment variable: {name}")
        sys.exit(1)
    try:
        return cast(value)
    except Exception:
        print(f"❌ Failed to cast environment variable: {name}")
        sys.exit(1)

TOKEN = get_env_var('BOT_TOKEN')
MESSAGE_ID = get_env_var('MESSAGE_ID', int)
CHANNEL_ID = get_env_var('CHANNEL_ID', int)
CATEGORY_ID = get_env_var('CATEGORY_ID', int)
OWNER_ID = get_env_var('OWNER_ID', int)

# ---------------------------
# Discord bot setup
# ---------------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user}")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != MESSAGE_ID:
        return
    if str(payload.emoji) != "✅":
        return

    try:
        guild = bot.get_guild(payload.guild_id) or await bot.fetch_guild(payload.guild_id)
        user = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not guild or not user or user.bot:
            return

        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if not category:
            print("❌ Category not found.")
            return

        channel_name = f"vip-{user.name}".replace(" ", "-").lower()

        # Check if channel already exists
        existing_channel = discord.utils.get(category.channels, name=channel_name)
        if existing_channel:
            await existing_channel.send(f"👋 Welcome back <@{user.id}>! Your channel is still here.")
            print(f"⚠ Channel already exists for {user.name}, sent welcome back.")
            return

        # Create new channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_member(OWNER_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        private_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category
        )

        await private_channel.send(
            f"Hey <@{user.id}>! Welcome — let me know which channel you're looking to unlock 🔓"
        )

        # Schedule deletion after 2 days
        async def delete_after_delay():
            await asyncio.sleep(172800)  # 2 days
            try:
                if private_channel.category and private_channel.category.id == CATEGORY_ID:
                    await private_channel.delete()
            except discord.NotFound:
                pass

        bot.loop.create_task(delete_after_delay())

    except Exception:
        print("❌ Error in on_raw_reaction_add:")
        traceback.print_exc()

# ---------------------------
# Crash-safe bot runner
# ---------------------------
async def run_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            traceback.print_exc()
            print("⏳ Restarting in 5 minutes...")
            await asyncio.sleep(300)  # Wait 5 minutes before retry

# ---------------------------
# Start everything
# ---------------------------
if __name__ == "__main__":
    keep_alive()
    asyncio.run(run_bot())
