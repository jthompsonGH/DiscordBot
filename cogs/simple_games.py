import discord
from discord import app_commands
from discord.ext import commands
from games.rock_paper_scissors import RockPaperScissors, getRPSEmbed
from games.tic_tac_toe import TicTacToe

class Games(commands.Cog):
    client : commands.Bot

    def __init__(self, client):
        self.client = client

    @app_commands.command(description="Play a round of Rock Paper Scissors against the targeted individual")
    @app_commands.describe(opponent="Who you'll play against")
    async def rps(self, interaction: discord.Interaction, opponent:discord.User):
        if opponent is None:
            await interaction.response.send_message("Could not find opponent.", ephemeral=True)
            return
        
        if opponent == interaction.user:
            await interaction.response.send_message("You can't play rock paper scissors with yourself.", ephemeral=True)
            return
        
        view = RockPaperScissors(player1=interaction.user, player2=opponent, timeout=60)
        embed = getRPSEmbed(view=view)

        await interaction.response.send_message(f"{interaction.user.mention} has challenged {opponent.mention} to ROCK PAPER SCISSORS", embed=embed, view=view, allowed_mentions=discord.AllowedMentions(users=[opponent, interaction.user]))
        message = await interaction.original_response()
        view.message = message
        view.embed = embed
        
        await view.wait()

    @app_commands.command(description="Play a round of Tic Tac Toe against the targeted individual")
    @app_commands.describe(opponent="Who you'll play against")
    async def ttt(self, interaction: discord.Interaction, opponent:discord.User):
        if opponent is None:
            await interaction.response.send_message("Could not find opponent.", ephemeral=True)
            return
        
        if opponent == interaction.user:
            await interaction.response.send_message("You can't play tic tac toe with yourself.", ephemeral=True)
            return
        
        await interaction.response.send_message(f"{interaction.user.mention} has challenged {opponent.mention} to TIC TAC TOE", allowed_mentions=discord.AllowedMentions(users=[opponent, interaction.user]))

        view = TicTacToe(timeout=90, player1=interaction.user, player2=opponent)

        await view.send_messages(interaction=interaction)
        
        await view.wait()

async def setup(client: commands.Bot):
    await client.add_cog(Games(client))