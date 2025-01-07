from .bot import bot
from .commands import setup as setup_commands

async def main():
    await setup_commands(bot)
    await bot.start()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())