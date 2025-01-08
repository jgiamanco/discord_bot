import discord
from discord.ext import commands
from utils.decorators import has_required_role
from database.manager import db_manager
import json
import sqlite3
import re
import random
import asyncio
from openai import OpenAI
from utils.decorators import get_server_role
from config import Config

print(Config.OPENAI_API_KEY)
# Initialize the OpenAI client with the API key from the Config class
client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
)

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'BasicCommands cog loaded')

    @bot.tree.command(name='hello', description='Says hello to the user.')
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hello, {interaction.user.mention}!')

    @bot.tree.command(name='add', description='Adds two numbers.')
    async def add(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f'The sum of {a} and {b} is {a + b}.')

    @bot.tree.command(name='subtract', description='Subtracts two numbers.')
    async def subtract(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f'The difference between {a} and {b} is {a - b}.')

    @bot.tree.command(name='multiply', description='Multiplies two numbers.')
    async def multiply(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f'The product of {a} and {b} is {a * b}.')

    @bot.tree.command(name='divide', description='Divides two numbers.')
    async def divide(self, interaction: discord.Interaction, a: int, b: int):
        if b == 0:
            await interaction.response.send_message('Cannot divide by zero!')
        else:
            await interaction.response.send_message(f'The result of {a} divided by {b} is {a / b}.')

    @bot.tree.command(name='repeat', description='Repeats the user\'s message.')
    async def repeat(self, interaction: discord.Interaction, *, message: str):
        await interaction.response.send_message(message)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.bot.user:
            return

        # if message.content.startswith('Image'):
        #     user_message = message.content[len('Image '):]

        #     response = client.images.generate(
        #         model="dall-e-3",
        #         prompt=user_message,
        #         size="1024x1024",
        #         quality="standard",
        #         n=1,
        #     )

        #     await message.channel.send(response.data[0].url)
        # else:
        #     await message.channel.send("Sorry my friend, I couldn't find a suitable response for your query.")
        
        if message.content.startswith('Mithrandir'):
            user_message = message.content[len('Mithrandir '):]
            
            # Generate a response using OpenAI
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                store=True,
                messages=[
                    {"role": "developer", "content": "You are a helpful and wise assistant that answers all prompts as if you are Gandalf from Lord of the Rings"},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500  # This limits the response to 300 tokens
            )
            
            # Extract the response text using regex
            response_str = str(response)
            match = re.search(r"content='(.*?)'", response_str, re.DOTALL)
            if match:
                ai_response = match.group(1).replace('\\n', '\n').strip()
                
                # Split the response into chunks of 1990 characters or less and add "..." at the end of each chunk except the last one
                chunks = [ai_response[i:i+1990] for i in range(0, len(ai_response), 1990)]
                
                for i, chunk in enumerate(chunks):
                    if i < len(chunks) - 1:
                        await message.channel.send(chunk + "...")
                    else:
                        await message.channel.send(chunk)
            else:
                await message.channel.send("Sorry my friend, I couldn't find a suitable response for your query.")

        # Normalize the case of the message content
        normalized_content = message.content.lower()

        emoji_pattern = re.compile(r'\\u[\dA-Fa-f]{4}')
        
        match = re.search(r'(\d+)([fc])', normalized_content)
        if match:
            temp = int(match.group(1))
            unit = match.group(2)

            if unit == 'f':
                # Convert Fahrenheit to Celsius
                celsius = (temp - 32) * 5.0/9.0
                response = f'{temp}F is {celsius:.2f}C'
            elif unit == 'c':
                # Convert Celsius to Fahrenheit
                fahrenheit = (temp * 9.0/5.0) + 32
                response = f'{temp}C is {fahrenheit:.2f}F'
            await message.channel.send(response)

        # Check if the server-specific table exists
        server_id = message.guild.id
        db_manager.create_server_tables(server_id)

        # Look for the response in the server-specific table
        with db_manager.get_cursor() as cursor:
            cursor.execute(f'SELECT response_type, response_content FROM responses_{server_id} WHERE word = ?', (normalized_content,))
            row = cursor.fetchone()

        # If no response found, use the default responses table
        if not row:
            with db_manager.get_cursor() as cursor:
                cursor.execute('SELECT response_type, response_content FROM responses WHERE word = ?', (normalized_content,))
                row = cursor.fetchone()
        def replace_bracketed(match):
                    options = match.group(1).split(',')
                    return random.choice(options).strip().encode('utf-16', 'surrogatepass').decode('utf-16')
        
        if row:
            response_type, response_content = row
            if response_type == 'text':
                response_content = response_content.replace('%n', message.author.mention)
                response_content = response_content.replace('%dn', message.author.display_name)
                previous_messages = [msg async for msg in message.channel.history(limit=2)]
                if len(previous_messages) > 1:
                    previous_user = previous_messages[1].author
                    response_content = response_content.replace('%pn', previous_user.mention)
                    response_content = response_content.replace('%pdn', previous_user.display_name)
                response_content = re.sub(r'[\{\[](.*?)[\}\]]', replace_bracketed, response_content)
                await message.channel.send(emoji_pattern.sub(lambda x: chr(int(x.group(0)[2:], 16)), response_content))
            elif response_type == 'list':
                chosen_response = re.sub(r'[\{\[](.*?)[\}\]]', replace_bracketed, response_content)
                chosen_response = chosen_response.replace('%n', message.author.mention)
                chosen_response = chosen_response.replace('%dn', message.author.display_name)
                previous_messages = [msg async for msg in message.channel.history(limit=2)]
                if len(previous_messages) > 1:
                    previous_user = previous_messages[1].author
                    chosen_response = chosen_response.replace('%pn', previous_user.mention)
                    chosen_response = chosen_response.replace('%pdn', previous_user.display_name)
                await message.channel.send(emoji_pattern.sub(lambda x: chr(int(x.group(0)[2:], 16)), chosen_response))
            elif response_type == 'media':
                await message.channel.send(response_content)
        
        await self.bot.process_commands(message)

    @bot.tree.command(name='trigger', description='Adds a new trigger-response pair.')
    @has_required_role()
    async def trigger(self, interaction: discord.Interaction, word: str, *, response: str):
        word = word.lower()
        server_id = interaction.guild.id

        if word == '%i':
            word = response.lower()
            await interaction.response.send_message('Please upload the media file or GIF you want to use as a response.', ephemeral=True)

            def check(message):
                return message.author == interaction.user and (message.attachments or 'tenor.com' in message.content or 'giphy.com' in message.content)

            try:
                message = await self.bot.wait_for('message', check=check, timeout=60.0)
                if message.attachments:
                    media_url = message.attachments[0].url
                else:
                    media_url = message.content

                with db_manager.get_cursor() as cursor:
                    cursor.execute(f'INSERT INTO responses_{server_id} (word, response_type, response_content) VALUES (?, ?, ?)', (word, 'media', media_url))
                await interaction.followup.send(f'Added media response for word "{word}".', ephemeral=True)
            except asyncio.TimeoutError:
                await interaction.followup.send('You took too long to upload the media file or GIF.', ephemeral=True)
            except sqlite3.IntegrityError:
                await interaction.followup.send(f'The word "{word}" already has a response.', ephemeral=True)
        else:
            try:
                with db_manager.get_cursor() as cursor:
                    if '{' in response and '}' in response:
                        response_type = 'list'
                    else:
                        response_type = 'text'
                    
                    # Insert into the server-specific table
                    cursor.execute(f'INSERT INTO responses_{server_id} (word, response_type, response_content) VALUES (?, ?, ?)', (word, response_type, response))
                await interaction.response.send_message(f'Added text response for word "{word}".', ephemeral=True)
            except sqlite3.IntegrityError:
                await interaction.response.send_message(f'The word "{word}" already has a response.', ephemeral=True)

    @bot.tree.command(name='erase', description='Removes a trigger-response pair.')
    @has_required_role()
    async def erase(self, interaction: discord.Interaction, word: str):
        word = word.lower()
        server_id = interaction.guild.id

        with db_manager.get_cursor() as cursor:
            cursor.execute(f'DELETE FROM responses_{server_id} WHERE word = ?', (word,))
            if cursor.rowcount > 0:
                await interaction.response.send_message(f'Removed response for word "{word}".', ephemeral=True)
            else:
                await interaction.response.send_message(f'No response found for word "{word}".', ephemeral=True)

    @erase.error
    async def erase_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRole):
            await interaction.response.send_message('You do not have the required role to use this command.')

    @bot.tree.command(name='list', description='List all programmed triggers.')
    @has_required_role()
    async def list(self, interaction: discord.Interaction):
        server_id = interaction.guild.id

        with db_manager.get_cursor() as cursor:
            cursor.execute(f'SELECT word, response_content FROM responses_{server_id}')
            rows = cursor.fetchall()
            if rows:
                response_list = '\n'.join([f'{row["word"]}' for row in rows])
                await interaction.response.send_message(f'Here are the current triggers:\n{response_list}')
            else:
                await interaction.response.send_message('There are no programmed triggers.')

    @bot.tree.command(name='global_list', description='List all programmed triggers across all servers.')
    async def global_list(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        role_name = get_server_role(server_id)

        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role not in interaction.user.roles:
            await interaction.response.send_message('You do not have the required role to use this command.')
            return

        with db_manager.get_cursor() as cursor:
            cursor.execute('SELECT word, response_content FROM responses')
            rows = cursor.fetchall()
            if rows:
                response_list = '\n'.join([f'{row["word"]}: {row["response_content"]}' for row in rows])
                await interaction.response.send_message(f'Here are the global triggers:\n{response_list}')
            else:
                await interaction.response.send_message('There are no programmed triggers globally.')

    @bot.tree.command(name='help', description='Displays all available commands.')
    async def help(self, interaction: discord.Interaction):
        """Displays all available commands."""
        help_message = """
        Available Commands:
        `help` - Displays all available commands.
        `Mithrandir <ai_prompt>` - Asks Mithrandir to respond to a query.
        `set_admin_role <role>` - Sets the role required to use certain commands.
        `google <search_query>` - Searches Google for a specific term.
        `urban <term>` - Retrieves the definition and example of a Urban Dictionary term.
        `youtube <search_query>` - Retrieve a YouTube video from a link or search query.
        `hello` - Says hello to the user.
        `setwelcome <message>` - Sets a custom welcome message. (Can use set_admin_role to restrict to specific role.)
        `add <a> <b>` - Adds two numbers.
        `subtract <a> <b>` - Subtracts one number from another.
        `multiply <a> <b>` - Multiplies two numbers.
        `divide <a> <b>` - Divides one number by another.
        `repeat <message>` - Repeats the user's message.
        `serverinfo` - Displays server information.
        `userinfo <member>` - Displays user information.
        `trigger <word> <response>` - Sets a response for a specific word. (Can use set_admin_role to restrict to specific role.)
        `erase <word>` - Erases a response for a specific word in the trigger list. (Can use set_admin_role to restrict to specific role.)
        `lotr_game` - Guess who said that Lord of the Rings quote.
        `trivia` - Play a trivia game.
        `rps <rock|paper|scissors>` - Play rock, paper, scissors against the bot.
        `guess` - Play a guess the number game.
        `scramble` - Guess the scrambled word.
        `checkstars` - Check stars of user
        `addstars <user> <stars>` - Add stars to a user (Can use set_admin_role to restrict to specific role)
        `leaderboard` - Show the stars leaderboard
        `list` - Lists all saved triggers
        """
        await interaction.response.send_message(help_message)

async def setup(bot):
    await bot.add_cog(BasicCommands(bot))