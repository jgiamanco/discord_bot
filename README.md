# Mithrandir Discord Bot

Mithrandir is a versatile Discord bot designed to enhance your server with a variety of features including trivia games, search commands, custom responses, and more. This bot is built using the `discord.py` library and integrates with several APIs to provide a rich set of functionalities.

## Features

- **Trivia Games**: Play trivia games with questions from various categories and difficulties.
- **Search Commands**: Search Google, Urban Dictionary, and YouTube directly from Discord.
- **Custom Responses**: Set custom responses for specific words or phrases.
- **Welcome Messages**: Set custom welcome messages for new members.
- **Rock, Paper, Scissors**: Play rock, paper, scissors against the bot.
- **Guess the Number**: Play a guess the number game.
- **Scramble**: Guess the scrambled word.
- **Stars System**: Award stars to users and display a leaderboard.
- **Hand and Foot Card Game**: Play the Hand and Foot card game with your friends.

## Installation

1. **Clone the repository**:

   ```sh
   git clone https://github.com/yourusername/mithrandir-discord-bot.git
   cd mithrandir-discord-bot
   ```

2. **Create a virtual environment**:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies**:

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up the environment variables**:
   Create a `.env` file in the root directory and add the following variables:

   ```env
   DISCORD_TOKEN=your_discord_token
   ONE_RING_TOKEN=your_one_ring_token
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CX_KEY=your_google_cx_key
   API_NINJA_API_KEY=your_api_ninja_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

5. **Run the bot**:
   ```sh
   python app.py
   ```

## Usage

### Commands

- **General Commands**:

  - `/hello`: Says hello to the user.
  - `/add <a> <b>`: Adds two numbers.
  - `/subtract <a> <b>`: Subtracts two numbers.
  - `/multiply <a> <b>`: Multiplies two numbers.
  - `/divide <a> <b>`: Divides two numbers.
  - `/repeat <message>`: Repeats the user's message.
  - `/serverinfo`: Displays server information.
  - `/userinfo [member]`: Displays user information.

- **Trivia Commands**:

  - `/trivia`: Play a trivia game.
  - `/lotr_game`: Play a Lord of the Rings trivia game.

- **Search Commands**:

  - `/google <search_query>`: Searches Google for a specific term.
  - `/urban <term>`: Retrieves the definition and example of an Urban Dictionary term.
  - `/youtube <query>`: Retrieve a YouTube video from a link or search query.

- **Game Commands**:

  - `/rps <rock|paper|scissors>`: Play rock, paper, scissors against the bot.
  - `/guess`: Play a guess the number game.
  - `/scramble`: Guess the scrambled word.

- **Custom Responses**:

  - `/trigger <word> <response>`: Sets a response for a specific word.
  - `/erase <word>`: Erases a response for a specific word.
  - `/list`: Lists all saved triggers.
  - `/global_list`: Lists all programmed triggers across all servers.

- **Stars System**:

  - `/checkstars <user>`: Check how many stars a user has.
  - `/addstars <user> <stars>`: Add stars to a user.
  - `/leaderboard`: Display the top 10 users with the most stars.

- **Admin Commands**:

  - `/set_admin_role <role>`: Set the role required to use certain commands.
  - `/set_welcome <message>`: Sets a custom welcome message for the server.

- **Hand and Foot Card Game**:
  - `/startgame`: Starts a new game of Hand and Foot.
  - `/join`: Join an existing game.
  - `/deal`: Deal cards to all players.
  - `/draw`: Draw a card from the stock.
  - `/discard <card>`: Discard a card.
  - `/meld <cards>`: Meld cards.
  - `/suggest_melds`: Suggest playable melds.
  - `/goout`: Go out and end the round.
  - `/endgame`: End the current game.
  - `/show_table`: Show the current state of the game.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any improvements or new features to add.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

- [discord.py](https://github.com/Rapptz/discord.py)
- [OpenAI](https://www.openai.com/)
- [Open Trivia Database](https://opentdb.com/)
- [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)
- [Urban Dictionary API](https://www.urbandictionary.com/)

---

Feel free to customize this `README.md` file to better suit your project's needs.
