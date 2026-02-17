import discord
import os
import globals
from discord import app_commands
from discord.ext import commands

class Maintenance(commands.Cog):
    client: commands.Bot

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        if not globals.is_dev: return
        
        await self.client.tree.sync()
        print("Maintenance synced")

    @app_commands.command(description="Sync the bot's commands. Only for Josh")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != int(os.environ.get("DEV_USER_ID")):
            await interaction.response.send_message("Only Josh can use this command", ephemeral=True)
            return

        await self.client.tree.sync()


async def setup(client: commands.Bot):
    await client.add_cog(Maintenance(client))