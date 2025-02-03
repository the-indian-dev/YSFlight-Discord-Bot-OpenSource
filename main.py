import discord

import asyncpg
import asyncio

import logging
import os

bot = discord.Bot(intents=discord.Intents.all())

logging.basicConfig(format='%(name)s\t%(levelname)s\t\t%(message)s', level=logging.INFO)


# Connect to our Database
async def create_db_pool():
    bot.db = await asyncpg.create_pool(
        dsn='Postgres data str')
    logging.info("Connection Successful")


# Load all the cogs
bot.load_extension("cog.main")         # Main Cog containing the General commands and event
bot.load_extension("cog.ysflight")     # Cog containing YSFlight related functions
bot.load_extension("cog.chat")         # Cog containing the Chat-Sync Related commands


# Status Task
async def status_task():
    while True:
        await bot.change_presence(activity=discord.Game(name="YSFlight Vulkan"))
        await asyncio.sleep(10)
        await bot.change_presence(activity=discord.Game(name="/help for help"))
        await asyncio.sleep(10)
        await bot.change_presence(activity=discord.Game(name="Now with Slash commands!"))
        await asyncio.sleep(10)


# On successful login
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    bot.loop.create_task(status_task())

bot.loop.run_until_complete(create_db_pool())

if os.environ['deploy'] == "PROD":
    bot.run('prod_key')  # PRODUCTION
else:
    bot.run('test_key')  # TESTING
