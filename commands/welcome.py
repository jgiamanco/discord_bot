import discord
from discord.ext import commands
from utils.decorators import has_required_role, error_handler
from database.manager import db_manager

class WelcomeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.channels, name='general')
        if not channel:
            return

        server_id = member.guild.id
        table_name = f'responses_{server_id}'

        with db_manager.get_cursor() as cursor:
            # Check if the custom table exists
            cursor.execute(
                f'''
                SELECT response_content
                FROM {table_name}
                WHERE word = 'welcome_message'
                AND response_type = 'welcome'
                '''
            )
            result = cursor.fetchone()

            # If custom table doesn't exist or no result, fallback to default table
            if not result:
                cursor.execute(
                    '''
                    SELECT response_content
                    FROM responses
                    WHERE word = 'welcome_message'
                    AND response_type = 'welcome'
                    '''
                )
                result = cursor.fetchone()

            welcome_message = (
                result['response_content'] if result
                else f'Welcome to the server, {member.mention}!'
            )

        await channel.send(welcome_message)

    @bot.tree.command(
        name='set_welcome',
        description='Sets a custom welcome message for the server.'
    )
    @has_required_role()
    @error_handler()
    async def set_welcome(
        self,
        interaction: discord.Interaction,
        message: str
    ):
        server_id = interaction.guild.id
        table_name = f'responses_{server_id}'

        with db_manager.get_cursor() as cursor:
            # Ensure the custom table exists
            cursor.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    word TEXT PRIMARY KEY,
                    response_type TEXT,
                    response_content TEXT
                )
                '''
            )
            cursor.execute(
                f'''
                INSERT INTO {table_name} (word, response_type, response_content)
                VALUES (?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET response_content=excluded.response_content
                ''',
                ('welcome_message', 'welcome', message)
            )

        await interaction.response.send_message('Custom welcome message set!')

async def setup(bot):
    await bot.add_cog(WelcomeCommands(bot))