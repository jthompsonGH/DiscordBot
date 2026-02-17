import discord
import typing
import sys
import os
import data
from discord import app_commands
from discord.ext import commands
from devlogs import *

class DevlogCommands(commands.GroupCog, group_name='devlog', group_description='Commands to add / list devlogs'):
    client : commands.Bot
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            data.instance.devlog_lists = loadDevlogs()

            for list in data.instance.devlog_lists:
                print(f"Devlogs loaded: {list.title}")
        except Exception as e:
            print('There was an error loading devlogs. Error: ' + str(e))
            print('Closing bot.')
            sys.exit('Failed_to_load')

        print("Devlogs loaded")

    async def title_autocompletion(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:

        choices = []
        for list in data.instance.devlog_lists:
            if current.lower() in list.title.lower():
                choices.append(app_commands.Choice(name=list.title, value=list.title))
        if len(choices) > 25:
            choices = choices[:25]
        return choices

    @app_commands.command(name="add", description="Add a devlog to the given list (Josh only)")
    @app_commands.describe(title="What list to add this log to")
    @app_commands.autocomplete(title=title_autocompletion)
    async def add(self, interaction: discord.Interaction, title:str):
        if interaction.user.id != int(os.environ.get("DEV_USER_ID")):
            await interaction.response.send_message("Only Josh can use this command", ephemeral=True)
            return

        await interaction.response.send_modal(DevlogModal(data.instance.devlog_lists, title))

    @app_commands.command(name="list", description="Check a devlog list")
    @app_commands.describe(title="What list to look at")
    @app_commands.autocomplete(title=title_autocompletion)
    async def list(self, interaction: discord.Interaction, title:str):
        devlog_list = None

        for d in data.instance.devlog_lists:
            if d.title.lower() == title.lower():
                devlog_list = d

        if devlog_list is None:
            await interaction.response.send_message("Could not find devlog list with that title.", ephemeral=True)
            return
        
        if len(devlog_list.logs) == 1:
            embed = getDevlogEmbed(devlog_list.logs[0], devlog_list.title, self.client.user, None, None)
            await interaction.response.send_message(embed=embed)
            return
        
        embed = getDevlogEmbed(devlog_list.logs[0], devlog_list.title, self.client.user, 1, len(devlog_list.logs))
        
        view = DevlogView(timeout=90, list=devlog_list, embed=embed, bot=self.client)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

        await view.wait()
    
async def setup(client: commands.Bot):
    await client.add_cog(DevlogCommands(client))
