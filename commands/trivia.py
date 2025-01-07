import discord
from discord.ext import commands
import requests
import html
import random
from utils.decorators import error_handler
from commands.info import InfoCommands

class TriviaCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.info_commands = InfoCommands(bot)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @bot.tree.command(name='trivia', description='Play a trivia game.')
    @error_handler()
    async def trivia(self, interaction: discord.Interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        categories_response = requests.get("https://opentdb.com/api_category.php")
        categories_data = categories_response.json()
        categories = {cat['name'].lower(): cat['id'] for cat in categories_data['trivia_categories']}

        await interaction.response.send_message("Please enter the category:")
        category_msg = await self.bot.wait_for('message', check=check)
        category = category_msg.content.lower()

        if "entertainment" in category:
            await interaction.followup.send("Please specify the medium (Books, Film, Music, etc.):")
            medium_msg = await self.bot.wait_for('message', check=check)
            medium = medium_msg.content.lower()
            category = f"entertainment: {medium}"

        matched_category = next((cat_name for cat_name in categories if category in cat_name), None)
        if not matched_category:
            await interaction.followup.send("Invalid category. Please try again.")
            return

        category_id = categories[matched_category]

        await interaction.followup.send("Please enter the difficulty (easy, medium, hard):")
        difficulty_msg = await self.bot.wait_for('message', check=check)
        difficulty = difficulty_msg.content.lower()

        await interaction.followup.send("Please enter the number of questions:")
        num_questions_msg = await self.bot.wait_for('message', check=check)
        num_questions = num_questions_msg.content

        url = f"https://opentdb.com/api.php?amount={num_questions}&category={category_id}&difficulty={difficulty}"
        response = requests.get(url)
        data = response.json()

        if data['response_code'] != 0:
            await interaction.followup.send("Sorry, there was an error fetching the questions.")
            return

        for question_data in data['results']:
            question = html.unescape(question_data['question'])
            correct_answer = html.unescape(question_data['correct_answer'])
            incorrect_answers = [html.unescape(ans) for ans in question_data['incorrect_answers']]
            all_answers = incorrect_answers + [correct_answer]
            random.shuffle(all_answers)

            options = {chr(65 + i): ans for i, ans in enumerate(all_answers)}
            options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])

            await interaction.followup.send(f"Question: {question}\nOptions:\n{options_text}")

            answer_msg = await self.bot.wait_for('message', check=check)
            user_answer = answer_msg.content.strip().upper()

            if user_answer in options and options[user_answer] == correct_answer:
                await interaction.followup.send("Correct!")
                await self.info_commands.add_stars(interaction, interaction.user, 1)
            elif user_answer.lower() == correct_answer.lower():
                await interaction.followup.send("Correct!")
                await self.info_commands.add_stars(interaction, interaction.user, 1)
            else:
                await interaction.followup.send(f"Incorrect. The correct answer was: {correct_answer}")

        await interaction.followup.send("Trivia game over! Thanks for playing.")

async def setup(bot):
    await bot.add_cog(TriviaCommands(bot))