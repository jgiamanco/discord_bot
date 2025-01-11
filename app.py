import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils.logger import logger
from config import Config
from commands import setup

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='>', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    for guild in bot.guilds:
        logger.info(f'Connected to server: {guild.name} (ID: {guild.id})')
    await bot.tree.sync()
    logger.info('Commands synced successfully.')

async def main():
    await setup(bot)  # Load all cogs
    async with bot:
        logger.info(f"Starting Discord bot {Config.VERSION}")
        await bot.start(Config.DISCORD_TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())