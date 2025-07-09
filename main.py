from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
    
import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load secrets
TOKEN = os.environ['BOT_TOKEN']
MESSAGE_ID = int(os.environ['MESSAGE_ID'])
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
CATEGORY_ID = int(os.environ['CATEGORY_ID'])
OWNER_ID = int(os.environ['OWNER_ID'])

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != MESSAGE_ID:
        return
    if str(payload.emoji) != "✅":
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    if user.bot:
        return

    category = discord.utils.get(guild.categories, id=CATEGORY_ID)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.get_member(OWNER_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel_name = f"vip-{user.name}".replace(" ", "-").lower()
    private_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category)
    await private_channel.send(f"Hey <@{user.id}>! Welcome — let me know which channel you're looking to unlock 🔓")

    # Auto-delete after 2 days (172800 seconds)
    await asyncio.sleep(172800)
    await private_channel.delete()

keep_alive()
bot.run(TOKEN)