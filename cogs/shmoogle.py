import discord
import typing
import sys
import random as rand
import data
from discord import app_commands
from discord.ext import commands
from shmoogle import *

class Shmoogle(commands.Cog):
    client: commands.Bot

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            data.instance.shmoogle_lists = loadTrackerLists()

            guilds : typing.List[discord.Guild] = []
            async for guild in self.client.fetch_guilds():
                guilds.append(guild)

            for server in data.instance.shmoogle_lists:
                for guild in guilds:
                    if guild.id == server.guild_id:
                        server.guild_name = guild.name

                print(f"Shmoogles loaded: {server.guild_name} (id: {server.guild_id})")
        except Exception as e:
            print('There was an error loading shmoogles. Error: ' + str(e))
            print('Closing bot.')
            sys.exit('Failed_to_load')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        shmoogled = False
        shmoogle_chance = rand.randint(0, 99)
        print(f"    shmoogle rolled: {shmoogle_chance}")
        if shmoogle_chance < 2:
            await message.channel.send("shmoogle")
            shmoogled = True

        if shmoogled:
            server = None
            tracker = None
            for s in data.instance.shmoogle_lists:
                if s.guild_id == message.guild.id:
                    server = s
            
            if server is None:
                server = ShmoogleList(message.guild.id, message.guild.name, [])
                data.instance.shmoogle_lists.append(server)
            
            for t in server.trackers:
                if t.user_id == message.author.id:
                    tracker = t

            if tracker is None:
                tracker = ShmoogleTracker(message.author.id, 0)
                server.add_tracker(tracker)

            tracker.increment()

            saveTrackerLists(data.instance.shmoogle_lists)

    @app_commands.command(description="Shows how many times the target user has been shmoogled")
    @app_commands.describe(user="User to check")
    async def shmoogle(self, interaction: discord.Interaction, user: discord.User):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        
        guild = None
        for g in data.instance.shmoogle_lists:
            if g.guild_id == interaction.guild_id:
                guild = g

        if guild is None:
            await interaction.response.send_message("No one has been shmoogled in this server yet 😢")
            return
        
        tracker = None
        for t in guild.trackers:
            if t.user_id == user.id:
                tracker = t

        if tracker is None:
            await interaction.response.send_message(f"{user.mention} hasn't been shmoogled yet", allowed_mentions=discord.AllowedMentions(users=[user]))
            return
        
        await interaction.response.send_message(f"{user.mention} has been shmoogled **{tracker.count}** {'time' if tracker.count == 1 else 'times'}!", allowed_mentions=discord.AllowedMentions(users=[user]))

    @app_commands.command(description="Shmoogle Leaderboard")
    async def shleaderboard(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        
        guild_data = None
        for g in data.instance.shmoogle_lists:
            if g.guild_id == interaction.guild_id:
                guild_data = g

        if guild_data is None:
            await interaction.response.send_message("No one has been shmoogled in this server yet 😢")
            return
        
        leaderboard_string = ""
        leading_tracker = guild_data.trackers[0]
        
        guild_data.trackers.sort(key=lambda tracker: tracker.count, reverse=True)
        
        for index, t in enumerate(guild_data.trackers):
            user = interaction.guild.get_member(t.user_id)
            leaderboard_string += f"{index + 1}. ***{user.name}*** - {t.count}\n"

            if t.count > leading_tracker.count:
                leading_tracker = t

        embed = discord.Embed(title="The Shleaderboard", color=discord.Color.dark_gold(), description=leaderboard_string)

        leading_user = interaction.guild.get_member(leading_tracker.user_id)

        embed.set_footer(icon_url=leading_user.avatar.url, text=f"{leading_user.name} is in the lead!")

        await interaction.response.send_message(embed=embed)


async def setup(client: commands.Bot):
    await client.add_cog(Shmoogle(client))
