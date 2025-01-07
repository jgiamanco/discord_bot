import discord
import random
from discord.ext import commands
from database.manager import db_manager

class Player:
    def __init__(self, user):
        self.user = user
        self.hand = []
        self.foot = []
        self.melds = []
        self.score = 0

class Team:
    def __init__(self, name):
        self.name = name
        self.players = []
        self.melds = []
        self.played_down = False

class HandFoot:
    def __init__(self, channel, server_id):
        self.channel = channel
        self.server_id = server_id
        self.players = []
        self.teams = []
        self.deck = self.create_deck()
        self.current_turn = 0
        self.round_over = False
        self.discard_pile = []
        self.create_game_table()

    def create_game_table(self):
        table_name = f'games_{self.server_id}'
        with db_manager.get_cursor() as cursor:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    player_name TEXT,
                    hand TEXT,
                    foot TEXT,
                    melds TEXT,
                    score INTEGER,
                    current_turn INTEGER,
                    discard_pile TEXT
                )
            ''')

    def save_game_state(self):
        table_name = f'games_{self.server_id}'
        with db_manager.get_cursor() as cursor:
            cursor.execute(f'DELETE FROM {table_name}')
            for player in self.players:
                cursor.execute(f'''
                    INSERT INTO {table_name} (player_id, player_name, hand, foot, melds, score, current_turn, discard_pile)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    player.user.id,
                    player.user.name,
                    ','.join(map(str, player.hand)),
                    ','.join(map(str, player.foot)),
                    ';'.join(','.join(map(str, meld)) for meld in player.melds),
                    player.score,
                    self.current_turn,
                    ','.join(map(str, self.discard_pile))
                ))

    def load_game_state(self):
        table_name = f'games_{self.server_id}'
        with db_manager.get_cursor() as cursor:
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = cursor.fetchall()
            for row in rows:
                player = Player(discord.Object(id=row['player_id']))
                player.user.name = row['player_name']
                player.hand = list(map(int, row['hand'].split(',')))
                player.foot = list(map(int, row['foot'].split(',')))
                player.melds = [list(map(int, meld.split(','))) for meld in row['melds'].split(';') if meld]
                player.score = row['score']
                self.players.append(player)
            self.current_turn = rows[0]['current_turn'] if rows else 0
            self.discard_pile = list(map(int, rows[0]['discard_pile'].split(','))) if rows else []

    def clear_game_state(self):
        table_name = f'games_{self.server_id}'
        with db_manager.get_cursor() as cursor:
            cursor.execute(f'DELETE FROM {table_name}')

    def create_deck(self):
        deck = [rank for rank in range(1, 14) for _ in range(4)] * 6 + [0] * 12  # 0 represents Jokers
        random.shuffle(deck)
        return deck

    def deal_cards(self):
        for player in self.players:
            player.hand = sorted([self.deck.pop() for _ in range(13)])
            player.foot = sorted([self.deck.pop() for _ in range(11)])

    def draw_card(self, player):
        player.hand.append(self.deck.pop())
        player.hand.append(self.deck.pop())
        player.hand.sort()

    def discard_card(self, player, card):
        player.hand.remove(card)
        self.discard_pile.append(card)
        self.draw_card(player)

    def meld(self, player, cards):
        meld_rank = cards[0]
        if meld_rank == 3:
            raise ValueError("Melds of 3's are not allowed")
        if all(card == meld_rank or card in [0, 2] for card in cards):
            if meld_rank in [0, 2] and len(cards) < 7:
                raise ValueError("Wild card melds must have 7 cards to be closed")
            player.melds.append(cards)
            for card in cards:
                player.hand.remove(card)
            # Add meld to the player's team melds
            team = self.get_team(player)
            if team is not None:
                team.melds.append(cards)
            else:
                raise ValueError("Player is not part of any team")
        else:
            raise ValueError("Invalid meld")

    def suggest_melds(self, player):
        hand = player.hand
        melds = []
        for rank in range(1, 14):
            if rank == 3:
                continue
            meld = [card for card in hand if card == rank or card in [0, 2]]
            if len(meld) >= 3 and meld.count(rank) > meld.count(0) + meld.count(2):
                melds.append(meld)
        return melds

    def calculate_meld_score(self, meld):
        score = 0
        for card in meld:
            if card == 0:
                score += 50
            elif card == 2:
                score += 20
            elif card == 1:
                score += 15
            elif 9 <= card <= 13:
                score += 10
            elif 4 <= card <= 8:
                score += 5
            elif card == 3:
                score += 0
        return score

    def get_play_down_score(self, team):
        total_score = sum(player.score for player in team.players)
        if total_score < 2000:
            return 50
        elif total_score < 4000:
            return 90
        elif total_score < 6000:
            return 120
        else:
            return 150

    def can_play_down(self, team, melds):
        if team.played_down:
            return True
        meld_score = sum(self.calculate_meld_score(meld) for meld in melds)
        return meld_score >= self.get_play_down_score(team)

    def can_go_out(self, player):
        red_books = sum(1 for meld in player.melds if len(meld) == 7 and all(card not in [0, 2] for card in meld))
        black_books = sum(1 for meld in player.melds if len(meld) == 7 and any(card in [0, 2] for card in meld))
        return red_books >= 1 and black_books >= 1 and not player.hand and not player.foot

    def score(self):
        scores = {team.name: 0 for team in self.teams}
        for team in self.teams:
            for meld in team.melds:
                if len(meld) == 7:
                    if all(card not in [0, 2] for card in meld):
                        scores[team.name] += 500
                    elif any(card in [0, 2] for card in meld):
                        scores[team.name] += 300
                for card in meld:
                    if card == 0:
                        scores[team.name] += 50
                    elif card == 2:
                        scores[team.name] += 20
                    elif card == 1:
                        scores[team.name] += 15
                    elif 9 <= card <= 13:
                        scores[team.name] += 10
                    elif 4 <= card <= 8:
                        scores[team.name] += 5
                    elif card == 3:
                        scores[team.name] -= 150
            for player in team.players:
                for card in player.hand + player.foot:
                    if card == 0:
                        scores[team.name] -= 50
                    elif card == 2:
                        scores[team.name] -= 20
                    elif card == 1:
                        scores[team.name] -= 15
                    elif 9 <= card <= 13:
                        scores[team.name] -= 10
                    elif 4 <= card <= 8:
                        scores[team.name] -= 5
                    elif card == 3:
                        scores[team.name] -= 150
        return scores

    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def current_player(self):
        return self.players[self.current_turn]

    def get_team(self, player):
        for team in self.teams:
            if player in team.players:
                return team
        return None

    def assign_teams(self):
        num_players = len(self.players)
        if num_players in [2, 4]:
            num_teams = 2
        elif num_players in [3, 5]:
            num_teams = num_players
        elif num_players == 6:
            num_teams = 3
        elif num_players == 7:
            num_teams = 7
        elif num_players == 8:
            num_teams = 4
        elif num_players == 9:
            num_teams = 3
        else:
            raise ValueError("Invalid number of players for team assignment")

        team_names = [f"Team {i+1}" for i in range(num_teams)]
        self.teams = [Team(name) for name in team_names]
        for i, player in enumerate(self.players):
            self.teams[i % num_teams].players.append(player)

    def determine_first_player(self):
        highest_card = -1
        first_player = None
        for player in self.players:
            card = self.deck.pop()
            if card > highest_card:
                highest_card = card
                first_player = player
        self.current_turn = self.players.index(first_player)

class CardsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = commands.Bot(command_prefix='>', intents=intents)

    @bot.tree.command(name="startgame", description="Starts a new game of Hand and Foot")
    async def startgame(self, interaction: discord.Interaction):
        if interaction.channel.id in self.games:
            await interaction.response.send_message("A game is already in progress in this channel.")
        else:
            game = HandFoot(interaction.channel, interaction.guild.id)
            self.games[interaction.channel.id] = game
            await interaction.response.send_message("A new game of Hand and Foot has started! Use /join to join the game.")

    @bot.tree.command(name="join", description="Join an existing game")
    async def join(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel. Use /startgame to start a new game.")
        else:
            game = self.games[interaction.channel.id]
            if any(player.user.id == interaction.user.id for player in game.players):
                await interaction.response.send_message("You are already in the game!")
            else:
                new_player = Player(interaction.user)
                game.players.append(new_player)
                await interaction.response.send_message(f"{interaction.user.name} has joined the game!")
                game.assign_teams()
                await interaction.channel.send("Teams have been assigned!")

    @bot.tree.command(name="deal", description="Deal cards to all players")
    async def deal(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel. Use /startgame to start a new game.")
        else:
            game = self.games[interaction.channel.id]
            if len(game.players) < 2:
                await interaction.response.send_message("At least 2 players are required to start the game.")
            else:
                game.deal_cards()
                game.determine_first_player()
                for player in game.players:
                    await player.user.send(f"Your hand: {player.hand}\n\nTo take your turn, use the following commands:\n- `/draw` to draw two cards\n- `/meld <cards>` to meld cards (e.g., `/meld 3,3,3`)\n- `/discard <card>` to discard a card (e.g., `/discard 5`)\n- `/show_table` to see the current state of the game\n- `/goout` to go out and end the round")
                await interaction.response.send_message(f"Cards have been dealt to all players! {game.current_player().user.name} goes first.")
                game.save_game_state()

    @bot.tree.command(name="draw", description="Draw a card from the stock")
    async def draw(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel. Use /startgame to start a new game.")
        else:
            game = self.games[interaction.channel.id]
            if game.current_player().user.id != interaction.user.id:
                await interaction.response.send_message("It's not your turn.")
                return
            player = game.current_player()
            game.draw_card(player)
            await interaction.response.send_message(f"{interaction.user.name} drew two cards.")
            await player.user.send(f"Your hand: {player.hand}\n\nTo take your turn, use the following commands:\n- `/draw` to draw two cards\n- `/meld <cards>` to meld cards (e.g., `/meld 3,3,3`)\n- `/discard <card>` to discard a card (e.g., `/discard 5`)\n- `/show_table` to see the current state of the game\n- `/goout` to go out and end the round")
            game.save_game_state()

    @bot.tree.command(name="discard", description="Discard a card")
    async def discard(self, interaction: discord.Interaction, card: int):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel. Use /startgame to start a new game.")
        else:
            game = self.games[interaction.channel.id]
            if game.current_player().user.id != interaction.user.id:
                await interaction.response.send_message("It's not your turn.")
                return
            player = game.current_player()
            game.discard_card(player, card)
            await interaction.response.send_message(f"{interaction.user.name} discarded a card.")
            await player.user.send(f"Your hand: {player.hand}\n\nTo take your turn, use the following commands:\n- `/draw` to draw two cards\n- `/meld <cards>` to meld cards (e.g., `/meld 3,3,3`)\n- `/discard <card>` to discard a card (e.g., `/discard 5`)\n- `/show_table` to see the current state of the game\n- `/goout` to go out and end the round")
            if not player.hand:
                player.hand = player.foot
                player.foot = []
                await player.user.send(f"Your foot: {player.hand}")
            game.next_turn()
            await interaction.channel.send(f"It's now {game.current_player().user.name}'s turn.")
            game.save_game_state()

    @bot.tree.command(name="meld", description="Meld cards")
    async def meld(self, interaction: discord.Interaction, cards: str):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel. Use /startgame to start a new game.")
        else:
            game = self.games[interaction.channel.id]
            if game.current_player().user.id != interaction.user.id:
                await interaction.response.send_message("It's not your turn.")
                return
            player = game.current_player()
            card_list = [int(card) for card in cards.split(",")]
            team = game.get_team(player)
            if not game.can_play_down(team, [card_list]):
                await interaction.response.send_message(f"Your team needs to meet the play down score of {game.get_play_down_score(team)} points.")
                return
            try:
                game.meld(player, card_list)
                await interaction.response.send_message(f"{interaction.user.name} melded cards.")
                await player.user.send(f"Your hand: {player.hand}\n\nTo take your turn, use the following commands:\n- `/draw` to draw two cards\n- `/meld <cards>` to meld cards (e.g., `/meld 3,3,3`)\n- `/discard <card>` to discard a card (e.g., `/discard 5`)\n- `/show_table` to see the current state of the game\n- `/goout` to go out and end the round")
                if not player.hand:
                    player.hand = player.foot
                    player.foot = []
                    await player.user.send(f"Your foot: {player.hand}")
                if not team.played_down:
                    team.played_down = True
                game.save_game_state()
            except ValueError as e:
                await interaction.response.send_message(str(e))

    @bot.tree.command(name="suggest_melds", description="Suggest playable melds")
    async def suggest_melds(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel.")
        else:
            game = self.games[interaction.channel.id]
            player = game.current_player()
            if player.user.id != interaction.user.id:
                await interaction.response.send_message("It's not your turn.")
                return
            melds = game.suggest_melds(player)
            if melds:
                await interaction.response.send_message(f"Suggested melds: {melds}")
            else:
                await interaction.response.send_message("No playable melds found.")

    @bot.tree.command(name="goout", description="Go out and end the round")
    async def goout(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel. Use /startgame to start a new game.")
        else:
            game = self.games[interaction.channel.id]
            if game.current_player().user.id != interaction.user.id:
                await interaction.response.send_message("It's not your turn.")
                return
            player = game.current_player()
            if game.can_go_out(player):
                scores = game.score()
                await interaction.response.send_message(f"{interaction.user.name} has gone out! Scores: {scores}")
                game.clear_game_state()
                del self.games[interaction.channel.id]
            else:
                await interaction.response.send_message("You cannot go out yet.")

    @bot.tree.command(name="endgame", description="End the current game")
    async def endgame(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel.")
        else:
            game = self.games[interaction.channel.id]
            game.clear_game_state()
            del self.games[interaction.channel.id]
            await interaction.response.send_message("The game has been ended.")

    @bot.tree.command(name="show_table", description="Show the current state of the game")
    async def show_table(self, interaction: discord.Interaction):
        if interaction.channel.id not in self.games:
            await interaction.response.send_message("No game is currently running in this channel.")
        else:
            game = self.games[interaction.channel.id]
            table_state = "Current Table State:\n"
            for team in game.teams:
                table_state += f"{team.name} melds: {team.melds}\n"
                for player in team.players:
                    table_state += f"  {player.user.name}'s melds: {player.melds}\n"
            await interaction.response.send_message(table_state)

async def setup(bot):
    await bot.add_cog(CardsCommands(bot))