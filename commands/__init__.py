from .admin import setup as setup_admin
from .basic import setup as setup_basic
from .games import setup as setup_games
from .info import setup as setup_info
from .trivia import setup as setup_trivia
from .welcome import setup as setup_welcome
from .search import setup as setup_search
from .cards import setup as setup_cards

async def setup(bot):
    await setup_admin(bot)
    await setup_basic(bot)
    await setup_games(bot)
    await setup_info(bot)
    await setup_trivia(bot)
    await setup_welcome(bot)
    await setup_search(bot)
    await setup_cards(bot)