import discord
from discord.ext import commands
from utils.decorators import has_required_role
from database.manager import db_manager

class InfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @bot.tree.command(name='serverinfo', description='Displays server information.')
    async def serverinfo(self, interaction: discord.Interaction):
        server = interaction.guild
        num_members = server.member_count
        await interaction.response.send_message(f'This server is called {server.name} and has {num_members} members.')

    @bot.tree.command(name='userinfo', description='Displays user information.')
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user
        await interaction.response.send_message(f'User: {member.name}\nID: {member.id}\nJoined at: {member.joined_at}')

    @bot.tree.command(name='checkstars', description='Check how many stars a user has.')
    async def checkstars(self, interaction: discord.Interaction, user: discord.User):
        server_id = interaction.guild.id
        table_name = f'stars_{server_id}'

        print(f"checkstars command invoked by {interaction.user.id} for user {user.id}")
        await interaction.response.defer()
        with db_manager.get_cursor() as cursor:
            cursor.execute(f"SELECT stars FROM {table_name} WHERE user_id = ?", (str(user.id),))
            result = cursor.fetchone()
            if result:
                await interaction.followup.send(f"{user.mention} has {result['stars']} stars!")
            else:
                await interaction.followup.send(f"{user.mention} has no stars yet.")

    @bot.tree.command(name='addstars', description='Add stars to a user.')
    @has_required_role()
    async def addstars(self, interaction: discord.Interaction, user: discord.User, stars: int):
        await interaction.response.defer()
        await self.add_stars(interaction, user, stars)

    @addstars.error
    async def addstars_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRole):
            await interaction.response.send_message('You do not have the required role to add stars.')

    @bot.tree.command(name='leaderboard', description='Display the top 10 users with the most stars.')
    async def leaderboard(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        table_name = f'stars_{server_id}'

        with db_manager.get_cursor() as cursor:
            cursor.execute(f"SELECT user_mention, stars FROM {table_name} ORDER BY stars DESC LIMIT 10")
            leaderboard = cursor.fetchall()
            if leaderboard:
                leaderboard_text = "Stars Leaderboard:\n"
                for i, (user_mention, stars) in enumerate(leaderboard, 1):
                    leaderboard_text += f"{i}. {user_mention} - {stars} stars\n"
                await interaction.response.send_message(leaderboard_text)
            else:
                await interaction.response.send_message("No stars awarded yet.")

    async def add_stars(self, interaction: discord.Interaction, user: discord.User, stars: int):
        server_id = interaction.guild.id
        table_name = f'stars_{server_id}'

        with db_manager.get_cursor() as cursor:
            # Ensure the custom table exists
            cursor.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    user_id TEXT PRIMARY KEY,
                    user_mention TEXT,
                    stars INTEGER
                )
                '''
            )
            
            # Check if the user already has stars
            cursor.execute(f"SELECT stars FROM {table_name} WHERE user_id = ?", (str(user.id),))
            result = cursor.fetchone()
            
            if result:
                new_stars = result['stars'] + stars
                if new_stars < 0:
                    new_stars = 0
                cursor.execute(f"UPDATE {table_name} SET stars = ? WHERE user_id = ?", (new_stars, str(user.id)))
            else:
                new_stars = stars
                cursor.execute(f"INSERT INTO {table_name} (user_id, user_mention, stars) VALUES (?, ?, ?)", (str(user.id), user.mention, stars))
        
        await interaction.followup.send(f"{user.mention} now has {new_stars} star(s)!")

async def setup(bot):
    await bot.add_cog(InfoCommands(bot))