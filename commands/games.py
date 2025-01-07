import discord
from discord.ext import commands
import random
import asyncio
import requests
import unidecode
from config import Config
from commands.info import InfoCommands  # Import add_stars function
from utils.decorators import error_handler

class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.info_commands = InfoCommands(bot)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @bot.tree.command(name='rps', description='Play Rock, Paper, Scissors')
    async def rps(self, interaction: discord.Interaction, choice: str):
        choices = ['rock', 'paper', 'scissors']
        if choice.lower() not in choices:
            await interaction.response.send_message('Please choose either rock, paper, or scissors!')
            return

        bot_choice = random.choice(choices)
        choice = choice.lower()

        if choice == bot_choice:
            result = "It's a tie!"
        elif (choice == 'rock' and bot_choice == 'scissors') or (choice == 'paper' and bot_choice == 'rock') or (choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            await self.info_commands.add_stars(interaction, interaction.user, 1)  # Make sure this matches your function name
        else:
            result = "I win!"

        await interaction.response.send_message(f'You chose {choice}, I chose {bot_choice}. {result}')

    @bot.tree.command(name='guess', description='Play a guess the number game')
    async def guess(self, interaction: discord.Interaction):
        number = random.randint(1, 100)
        await interaction.response.send_message("Guess a number between 1 and 100!")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        for _ in range(5):  # Allow 5 guesses
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                guess = int(msg.content)
                if guess < number:
                    await interaction.channel.send("Higher!")
                elif guess > number:
                    await interaction.channel.send("Lower!")
                else:
                    await interaction.channel.send(f"Congrats {msg.author.mention}, you guessed the number!")
                    await self.info_commands.add_stars(interaction, interaction.user, 1)
                    return
            except asyncio.TimeoutError:
                await interaction.channel.send(f"Time's up! The correct number was: {number}")
                return
            except ValueError:
                await interaction.channel.send("Please enter a valid number.")

        await interaction.channel.send(f"Out of guesses! The correct number was: {number}")

    @bot.tree.command(name='scramble', description='Guess the scrambled word.')
    async def scramble(self, interaction: discord.Interaction):
        response = requests.get("https://api.api-ninjas.com/v1/randomword", headers={"X-Api-Key": Config.API_NINJA_API_KEY})
        word = response.json().get("word")[0]

        if not word:
            await interaction.response.send_message("Oops! Couldn't fetch a word. Try again later.")
            return

        word = word.capitalize()
        scrambled_word = ''.join(random.sample(word, len(word)))
        await interaction.response.send_message(f"Guess the word: {scrambled_word}")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            if guess.content.lower() == word.lower():
                await interaction.channel.send("Correct! 🎉")
                await self.info_commands.add_stars(interaction, interaction.user, 1)
        except asyncio.TimeoutError:
            await interaction.channel.send(f"Time's up! The correct word was {word}.")

    @bot.tree.command(name='lotr_game', description='Play a Lord of the Rings trivia game.')
    async def lotr_game(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            question, answer = get_lotr_trivia()
            await interaction.followup.send(f"Guess who says this Lord of the Rings quote: {question}")

            def check(m):
                return m.channel == interaction.channel and any(part in m.content.lower() for part in answer.lower().split())

            try:
                guess = await self.bot.wait_for('message', check=check, timeout=30.0)
                if guess:
                    await interaction.followup.send(f"Correct! The answer is indeed {answer}.")
                    await self.info_commands.add_stars(interaction, guess.author, 1)
                else:
                    await interaction.followup.send(f"Time's up! The correct answer was {answer}.")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"Time's up! The correct answer was {answer}.")
        except discord.errors.InteractionResponded as e:
            print(f"Error: {e}")
            await interaction.followup.send("Looks like this interaction was already responded to.")
        except Exception as e:
            await interaction.followup.send("Something went wrong with the interaction.")
            raise e

def get_character_name(character_id):
    response = requests.get(f'https://the-one-api.dev/v2/character/{character_id}', headers=Config.ONE_RING_HEADERS)
    
    try:
        data = response.json()
    except ValueError:
        raise Exception("Failed to parse JSON response")
    
    if response.status_code == 404:
        raise Exception(f"Character with ID {character_id} not found (404)")
    elif response.status_code != 200:
        raise Exception(f"Failed to fetch character data: {response.status_code} - {response.text}")
    
    if 'docs' in data and len(data['docs']) > 0:
        character_name = data['docs'][0]['name']
        if character_name == "MINOR_CHARACTER":
            raise KeyError("Character is a minor character")
        return character_name
    else:
        raise KeyError("Character name not found in the API response")

def get_lotr_trivia():
    response = requests.get('https://the-one-api.dev/v2/quote', headers=Config.ONE_RING_HEADERS)  # Replace with actual LOTR trivia API endpoint
    if response.status_code == 404:
        raise Exception("Trivia endpoint not found (404)")
    elif response.status_code != 200:
        raise Exception(f"Failed to fetch trivia data: {response.status_code} - {response.text}")
    
    data = response.json()
    
    if 'docs' in data and len(data['docs']) > 0:
        filtered_quotes = [quote for quote in data['docs'] if quote.get('character') != "MINOR_CHARACTER"]
        if not filtered_quotes:
            raise Exception("No valid trivia quotes found")
        
        random_index = random.randint(0, len(filtered_quotes) - 1)
        question = filtered_quotes[random_index]['dialog']  # Adjust according to the API response structure
        character_id = filtered_quotes[random_index]['character']
        
        try:
            character_name = get_character_name(character_id)
        except KeyError:
            return get_lotr_trivia()  # Retry if the character is a minor character
        
        return question, unidecode.unidecode(character_name)  # Normalize accents in the character name
    else:
        raise Exception("No trivia data found in the API response")

async def setup(bot):
    await bot.add_cog(GameCommands(bot))