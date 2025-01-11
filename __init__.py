from .app import app
from .commands import setup as setup_commands

async def main():
    await setup_commands(app)
    await app.start()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())