import discord
import typing
import sys
import random as rand
import data
from discord import app_commands
from discord.ext import commands
from anime import Anime, AnimeList, getAnimes, loadAnimeLists, filterAnimes, saveAnimeLists, backupAnimeLists, ListView, SingleView, RandomView, get_anime_embed

sort_by_choices = [
    app_commands.Choice(name="Title", value='title'),
    app_commands.Choice(name="Date Added", value='added'),
    app_commands.Choice(name="Recently Updated", value='updated')
]

class AnimeCommands(commands.Cog):
    client: commands.Bot

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            data.instance.anime_lists = loadAnimeLists()

            guilds : typing.List[discord.Guild] = []
            async for guild in self.client.fetch_guilds():
                guilds.append(guild)

            for server in data.instance.anime_lists:
                for guild in guilds:
                    if guild.id == server.guild_id:
                        server.guild_name = guild.name

                print(f"Shows loaded: {server.guild_name} (id: {server.guild_id}) \n    List length: {len(server.animes)}")
        except Exception as e:
            print('There was an error loading shows. Error: ' + str(e))
            print('Closing bot.')
            sys.exit('Failed_to_load')
        print("Shows loaded")
    
    @app_commands.command(description="Lists shows that fit the given filters")
    @app_commands.describe(status="What viewing status to show")
    @app_commands.describe(title_contains="Shows where the given phrase fits in the title")
    @app_commands.describe(sort_by="How to sort any found shows (defaults to Title)")
    @app_commands.choices(status=[
        app_commands.Choice(name="All", value='all'),
        app_commands.Choice(name="Planned", value='planned'),
        app_commands.Choice(name="Watching", value='watching'),
        app_commands.Choice(name="Watched", value='watched')
    ])
    @app_commands.choices(sort_by=sort_by_choices)
    async def list(self, interaction: discord.Interaction, status:app_commands.Choice[str], sort_by:typing.Optional[app_commands.Choice[str]],  title_contains:str=""):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        
        
        list_options = ['all', 'planned', 'watching', 'watched']
        sort_options = ['title', 'added', 'updated']
        if status.value not in list_options and status != "":
            await interaction.response.send_message("Please enter **all**, **planned**, **watching**, or **watched** as the status option.", ephemeral=True)
            return
        
        if sort_by == None:
            sort_by = app_commands.Choice(name="Title", value='title')
        
        if sort_by.value not in sort_options and sort_by != "":
            await interaction.response.send_message("Please enter **title**, **added**, or **updated** as the sorting option.", ephemeral=True)
            return
        
        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            await interaction.response.send_message("Could not find a list for this server.", ephemeral=True)
            return
        
        all_animes = getAnimes(server.animes, status.value, sort_by.value)

        if title_contains != "":
            all_animes = filterAnimes(all_animes, title_contains)

        if len(all_animes) == 0:
            await interaction.response.send_message(f"There were no shows in the list{f' marked **{status.value}**' if status.value != 'all' else ''}{f' with **{title_contains}** in the title.' if title_contains != '' else '.'}")
            return
        
        embed = get_anime_embed(all_animes[0], None if len(all_animes) == 1 else 1, len(all_animes), interaction.guild)
        view = None
        if len(all_animes) == 1:
            view = SingleView(180, all_animes[0], embed, interaction.guild)
        else:
            view = ListView(timeout=180, anime_list=all_animes, embed=embed, guild=interaction.guild)
        
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

        await view.wait()
        
    @app_commands.command(description="Find shows with titles that contain the given phrase")
    @app_commands.describe(title="Shows where the given phrase fits in the title")
    @app_commands.describe(sort_by="How to sort any found shows. (Title by default)")
    @app_commands.choices(sort_by=sort_by_choices)
    async def find(self, interaction: discord.Interaction, title:str, sort_by:typing.Optional[app_commands.Choice[str]]):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        
        if sort_by is None:
            sort_by = app_commands.Choice(name="Title", value='title')

        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            await interaction.response.send_message("Could not find a list for this server.", ephemeral=True)
            return
        
        all_animes = getAnimes(server.animes, 'all', sort_by.value)
        all_animes = filterAnimes(all_animes, title)

        if len(all_animes) == 0:
            await interaction.response.send_message(f"There were no shows in the list with **{title}** in the title.")
            return
        
        embed = get_anime_embed(all_animes[0], None if len(all_animes) == 1 else 1, len(all_animes), interaction.guild)
        view = None
        if len(all_animes) == 1:
            view = SingleView(180, all_animes[0], embed, interaction.guild)
        else:
            view = ListView(timeout=180, anime_list=all_animes, embed=embed, guild=interaction.guild)
        
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

        await view.wait()

    @app_commands.command(description="Add a new show to the list")
    @app_commands.describe(title="Title of the show. Be precise")
    @app_commands.describe(status="Current viewing status of this show. (Planned by default)")
    @app_commands.choices(status=[
        app_commands.Choice(name="Planned", value='planned'),
        app_commands.Choice(name="Watching", value='watching'),
        app_commands.Choice(name="Watched", value='watched')
    ])
    async def add(self, interaction: discord.Interaction, title:str, status:typing.Optional[app_commands.Choice[str]]):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return

        role = None
        if interaction.channel.guild is not None:
            role = discord.utils.get(interaction.user.roles, name="Anime Manager")

        if role is None:
            await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
            return
        
        if status == None:
            status = app_commands.Choice(name="Planned", value="planned")

        list_options = ['planned', 'watching', 'watched']
        if status.value not in list_options and status != "":
            await interaction.response.send_message("Please enter **planned**, **watching**, or **watched** as the status option.", ephemeral=True)
            return

        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            server = AnimeList(interaction.guild_id, interaction.guild.name, [])
            data.instance.anime_lists.append(server)
        
        all_animes = getAnimes(server.animes, status.value, None)

        animes_with_this_title = filterAnimes(all_animes, title, True)

        if len(animes_with_this_title) > 0:
            await interaction.response.send_message("This show is already in the list:\n", embed=get_anime_embed(animes_with_this_title[0], None, None, guild=interaction.guild))
            return

        new_anime = Anime.create(title, status.value, interaction.user.id)
        server.animes.append(new_anime)

        saveAnimeLists(data.instance.anime_lists)

        await interaction.response.send_message("Show added:\n", embed=get_anime_embed(new_anime, None, None, guild=interaction.guild))

    async def title_autocompletion(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> typing.List[app_commands.Choice[str]]:
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return


        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            await interaction.response.send_message("Could not find a list for this server.", ephemeral=True)
            return

        sorted_animes = getAnimes(server.animes, 'all', 'title')
        choices = []
        for anime in sorted_animes:
            if current.lower() in anime.title.lower():
                choices.append(app_commands.Choice(name=anime.title, value=anime.title))
        if len(choices) > 25:
            choices = choices[:25]
        return choices

    @app_commands.command(description="Update the status of a show, using its exact title (not case sensitive)")
    @app_commands.describe(title="Title of the show to update")
    @app_commands.describe(new_title="Optional new title for the show")
    @app_commands.describe(status="The new status of this show")
    @app_commands.choices(status=[
        app_commands.Choice(name="Planned", value='planned'),
        app_commands.Choice(name="Watching", value='watching'),
        app_commands.Choice(name="Watched", value='watched')
    ])
    @app_commands.autocomplete(title=title_autocompletion)
    async def update(self, interaction: discord.Interaction, title:str, status:app_commands.Choice[str], new_title:str=""):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        
        role = None
        if interaction.channel.guild is not None:
            role = discord.utils.get(interaction.user.roles, name="Anime Manager")

        if role is None:
            await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
            return

        list_options = ['planned', 'watching', 'watched']
        if status.value not in list_options and status != "":
            await interaction.response.send_message("Please enter **planned**, **watching**, or **watched** as the status option.", ephemeral=True)
            return

        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            await interaction.response.send_message("Could not find a list for this server.", ephemeral=True)
            return
        
        all_animes = getAnimes(server.animes, 'all', None)

        animes_with_this_title = filterAnimes(all_animes, title, True)

        if len(animes_with_this_title) == 0:
            await interaction.response.send_message("Could not find this show. Double check your spelling!")
            return

        if new_title != "" and title.lower() != new_title.lower():
            all_animes_newtitle = filterAnimes(all_animes, new_title, True)
            if len(all_animes_newtitle) > 0:
                await interaction.response.send_message(f"New title invalid, a show already exists with this title:\n", embed=get_anime_embed(all_animes_newtitle[0], None, None, guild=interaction.guild))
                return
        
        animes_with_this_title = filterAnimes(all_animes, title, True)

        if len(animes_with_this_title) > 1:
            await interaction.response.send_message("Somehow found more than one instance of a show with this title? Modifying the first one...")

        selected_anime = animes_with_this_title[0]

        if selected_anime.status == status.value:
            await interaction.response.send_message(f"This show is already marked as **{status.value}**")
            return

        selected_anime.updateStatus(status.value)

        if new_title != "":
            selected_anime.updateTitle(new_title)

        saveAnimeLists(data.instance.anime_lists)

        embed = get_anime_embed(selected_anime, None, None, interaction.guild)
        view = SingleView(180, selected_anime, embed, interaction.guild)

        await interaction.response.send_message("Show updated:\n", view=view, embed=embed)
        message = await interaction.original_response()
        view.message = message

        await view.wait()

    @app_commands.command(description="Remove a show from the list (not case sensitive)")
    @app_commands.describe(title="Title of the show to remove. Be precise")
    @app_commands.autocomplete(title=title_autocompletion)
    async def remove(self, interaction: discord.Interaction, title:str):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return

        role = None
        if interaction.channel.guild is not None:
            role = discord.utils.get(interaction.user.roles, name="Anime Manager")

        if role is None:
            await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
            return
        
        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            await interaction.response.send_message("Could not find a list for this server.", ephemeral=True)
            return
        
        all_animes = getAnimes(server.animes, 'all', None)

        animes_with_this_title = filterAnimes(all_animes, title, True)

        if len(animes_with_this_title) == 0:
            await interaction.response.send_message("Could not find this show. Double check your spelling!")
            return

        if len(animes_with_this_title) > 1:
            await interaction.response.send_message("Somehow found more than one instance of a show with this title? Removing the first one...")

        selected_anime = animes_with_this_title[0]

        server.animes.remove(selected_anime)

        saveAnimeLists(data.instance.anime_lists)

        await interaction.response.send_message(f"Show removed:\n", embed=get_anime_embed(selected_anime, None, None, guild=interaction.guild))

    @app_commands.command(description="Get a random planned show")
    async def random(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        

        server = None
        for s in data.instance.anime_lists:
            if s.guild_id == interaction.guild_id:
                server = s
        if server is None:
            await interaction.response.send_message("Could not find a list for this server.", ephemeral=True)
            return
        
        all_animes = getAnimes(server.animes, 'planned', None)

        if len(all_animes) == 0:
            await interaction.response.send_message("This server currently has no shows marked as **planned**.", ephemeral=True)
            return

        selected_anime = rand.choice(all_animes)

        embed = get_anime_embed(selected_anime, None, None, guild=interaction.guild)
        view = RandomView(timeout=180, anime=selected_anime, embed=embed, lists=data.instance.anime_lists, guild=interaction.guild)
        
        await interaction.response.send_message("You rolled:\n", embed=embed, view=view)
        message = await interaction.original_response()
        view.message = message

        await view.wait()

    @app_commands.command(description="Backup the server's data")
    async def backup(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.response.send_message("Couldn't find server ID. Aborting :/", ephemeral=True)
            return
        
        role = None
        if interaction.channel.guild is not None:
            role = discord.utils.get(interaction.user.roles, name="Anime Manager")

        if role is None:
            await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
            return

        await interaction.response.send_message(data.instance.doBackup())

    @app_commands.command(description="Pick one of two things")
    async def coinflip(self, interaction: discord.Interaction, heads:str, tails:str):
        result = rand.randint(0, 1)

        if result == 1:
            await interaction.response.send_message(f"**Tails!**\n    {tails}")
            return
        
        await interaction.response.send_message(f"**Heads!**\n    {heads}")

async def setup(client: commands.Bot):
    await client.add_cog(AnimeCommands(client))
