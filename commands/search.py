import discord
from discord.ext import commands
from discord import app_commands
from googleapiclient.discovery import build
import requests
import yt_dlp as youtube_dl
from config import Config

class SearchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @bot.tree.command(name='google', description='Searches Google for a specific term.')
    async def google(self, interaction: discord.Interaction, *, search_query: str):
        await interaction.response.defer()  # Acknowledge the interaction first
        
        service = build("customsearch", "v1", developerKey=Config.GOOGLE_API_KEY)
        res = service.cse().list(q=search_query, cx=Config.GOOGLE_CX_KEY, num=3).execute()
        
        search_results = res.get('items', [])

        if not search_results:
            await interaction.followup.send("No results found.")
            return

        response = "Top 3 Google search results:\n"
        for i, item in enumerate(search_results):
            response += f"{i+1}. [{item['title']}]({item['link']})\n"

        await interaction.followup.send(response)

    @bot.tree.command(name='urban', description='Retrieves the definition and example of a Urban Dictionary term.')
    async def urban(self, interaction: discord.Interaction, *, term: str):
        url = f"http://api.urbandictionary.com/v0/define?term={term}"
        response = requests.get(url)
        data = response.json()

        if data['list']:
            definition = data['list'][0]['definition']
            example = data['list'][0]['example']
            embed = discord.Embed(title=f"Urban Dictionary: {term}", description=definition, color=0x1D2439)
            embed.add_field(name="Example", value=example, inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No results found for {term}")

    @bot.tree.command(name="youtube", description="Retrieve a YouTube video from a link or search query")
    @app_commands.describe(query="The YouTube link or search query")
    async def youtube(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()  # Defer the response first
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch'
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(query, download=False)['entries'][0]
                video_url = info['webpage_url']
            except Exception as e:
                await interaction.followup.send("No video matching your request was found.")
                return

        await interaction.followup.send(video_url)

async def setup(bot):
    await bot.add_cog(SearchCommands(bot))