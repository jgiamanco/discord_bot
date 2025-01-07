import discord
from discord.ext import commands
from utils.decorators import error_handler
from database.manager import db_manager

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'AdminCommands cog loaded')

    @bot.tree.command(name='set_admin_role', description='Set the role required to use certain commands.')
    @commands.has_permissions(administrator=True)
    @error_handler()
    async def set_admin_role(self, interaction: discord.Interaction, role_name: str):
        server_id = interaction.guild.id
        with db_manager.get_cursor() as cursor:
            cursor.execute('INSERT OR REPLACE INTO server_roles (server_id, role_name) VALUES (?, ?)', (server_id, role_name))
        await interaction.response.send_message(f'The required role has been set to {role_name}.')

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))