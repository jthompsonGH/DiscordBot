from anime import AnimeComment, Anime, AnimeList, saveAnimeLists
from discord.ext import commands
import discord
import data
import typing


class AnimeView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=180 if timeout is None else timeout)

    async def update(self):
        pass

    async def update_children(self):
        pass

class RandomView(AnimeView):
    anime: Anime
    embed: discord.Embed
    message: discord.Message
    lists: typing.List[AnimeList]
    guild: discord.Guild
    comment_child: AnimeView

    def __init__(self, timeout, anime, embed, lists, guild):
        super().__init__(timeout=180 if timeout is None else timeout)
        self.anime = anime
        self.message = None
        self.embed = embed
        self.lists = lists
        self.guild = guild
        self.comment_child = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    async def disable(self):
        for item in self.children:
            item.disabled = True

    async def update(self):
        self.embed = get_anime_embed(self.anime, None, None, self.guild)
        await self.message.edit(embed=self.embed, view=self)

    async def update_children(self):
        if self.comment_child is not None:
            await self.comment_child.update()

    @discord.ui.button(label="Watching", style=discord.ButtonStyle.grey)
    async def set_watching(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.status_button_clicked('watching', interaction)
    
    @discord.ui.button(label="Watched", style=discord.ButtonStyle.grey)
    async def set_watched(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.status_button_clicked('watched', interaction)

    async def status_button_clicked(self, result: str, interaction: discord.Interaction):
        role = None
        if interaction.channel.guild is not None:
            role = discord.utils.get(interaction.user.roles, name="Anime Manager")

        if role is None:
            await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
            return
        
        self.anime.updateStatus(result)
        saveAnimeLists(data.instance.anime_lists)

        await self.disable()
        self.stop()

        await interaction.response.edit_message(view=self, embed=self.embed)

        new_embed = get_anime_embed(self.anime, None, None, self.guild)
        new_view = SingleView(180, self.anime, new_embed, self.guild)

        new_message = await interaction.followup.send(f"Updated to **{result}**:\n", view=new_view, embed=new_embed)
        new_view.message = new_message

        await new_view.wait()

    @discord.ui.button(label="Add Comment", style=discord.ButtonStyle.grey, row=3)
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(self.anime, self))

    @discord.ui.button(label="View Comments", style=discord.ButtonStyle.grey, row=4)
    async def view_comments(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.anime.comments) == 0:
            await interaction.response.send_message("This show has no comments yet.", ephemeral=True)
            return
        
        embed = get_comment_embed(self.anime, self.anime.comments[0], None if len(self.anime.comments) == 1 else 1, len(self.anime.comments), interaction.guild, interaction)
        view = None
        if len(self.anime.comments) > 1:
            view = CommentListView(180, self.anime, embed, interaction.guild, interaction, self)
        else:
            view = CommentSingleView(180, self.anime, embed, interaction.guild, interaction, self)

        self.comment_child = view
        
        await interaction.response.send_message(embed=embed, view=view)

        message = await interaction.original_response()
        view.message = message

        button.disabled = True
        await self.message.edit(view=self, embed=self.embed)

        await view.wait()

class SingleView(AnimeView):
    anime: Anime
    message: discord.Message
    embed: discord.Embed
    guild: discord.Guild
    comment_child: AnimeView

    def __init__(self, timeout, show, embed, guild):
        super().__init__(timeout=180 if timeout is None else timeout)
        self.value = None
        self.anime = show
        self.message = None
        self.embed = embed
        self.guild = guild
        self.comment_child = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    async def update(self):
        self.embed = get_anime_embed(self.anime, None, None, self.guild)
        await self.message.edit(embed=self.embed, view=self)

    async def update_children(self):
        if self.comment_child is not None:
            await self.comment_child.update()

    @discord.ui.button(label="Add Comment", style=discord.ButtonStyle.grey, row=3)
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(self.anime, self))

    @discord.ui.button(label="View Comments", style=discord.ButtonStyle.grey, row=4)
    async def view_comments(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.anime.comments) == 0:
            await interaction.response.send_message("This show has no comments yet.", ephemeral=True)
            return
        
        embed = get_comment_embed(self.anime, self.anime.comments[0], None if len(self.anime.comments) == 1 else 1, len(self.anime.comments), interaction.guild, interaction)
        view = None
        if len(self.anime.comments) > 1:
            view = CommentListView(180, self.anime, embed, interaction.guild, interaction, self)
        else:
            view = CommentSingleView(180, self.anime, embed, interaction.guild, interaction, self)
        
        await interaction.response.send_message(embed=embed, view=view)

        self.comment_child = view
        
        message = await interaction.original_response()
        view.message = message

        button.disabled = True
        await self.message.edit(view=self, embed=self.embed)

        await view.wait()

class ListView(AnimeView):
    anime_list: typing.List[Anime]
    viewing_comments: typing.List[str]
    message: discord.Message
    embed: discord.Embed
    guild: discord.Guild
    comment_children: dict[str, AnimeView]

    def __init__(self, timeout, anime_list, embed, guild):
        super().__init__(timeout=180 if timeout is None else timeout)
        self.value = None
        self.anime_list = anime_list
        self.viewing_comments = []
        self.current_index = 0
        self.message = None
        self.embed = embed
        self.guild = guild
        self.comment_children = {}

        if len(anime_list) == 1:
            for item in self.children:
                item.disabled = True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    async def update(self):
        self.embed = get_anime_embed(self.anime_list[self.current_index], self.current_index + 1, len(self.anime_list), self.guild)
        await self.message.edit(embed=self.embed, view=self)

    async def update_children(self):
        selected_anime = self.anime_list[self.current_index].title
        if selected_anime in self.comment_children.keys():
            await self.comment_children[selected_anime].update()
    
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.grey, row=2)
    async def full_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(-100, interaction)
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.grey, row=1)
    async def page_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(-5, interaction)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.grey, row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(-1, interaction)
        
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.grey, row=0)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(1, interaction)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.grey, row=1)
    async def page_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(5, interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.grey, row=2)
    async def full_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(100, interaction)

    async def change_page(self, amount: int, interaction: discord.Interaction):
        self.current_index += amount
        if amount == -100:
            self.current_index = 0
        elif amount == 100:
            self.current_index = len(self.anime_list) - 1

        self.current_index = max(0, min(self.current_index, len(self.anime_list) - 1))
        
        self.embed = get_anime_embed(self.anime_list[self.current_index], self.current_index + 1, len(self.anime_list), self.guild)
        await interaction.response.edit_message(view=self, embed=self.embed)

    @discord.ui.button(label="Add Comment", style=discord.ButtonStyle.grey, row=3)
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(self.anime_list[self.current_index], self))

    @discord.ui.button(label="View Comments", style=discord.ButtonStyle.grey, row=4)
    async def view_comments(self, interaction: discord.Interaction, button: discord.ui.Button):
        anime = self.anime_list[self.current_index]
        if len(anime.comments) == 0:
            await interaction.response.send_message("This show has no comments yet.", ephemeral=True)
            return
        
        if anime.title in self.viewing_comments:
            await interaction.response.send_message("Already showing comments for this show.", ephemeral=True)
            return
        
        embed = get_comment_embed(anime, anime.comments[0], None if len(anime.comments) == 1 else 1, len(anime.comments), interaction.guild, interaction)
        view = None
        if len(anime.comments) == 1:
            view = CommentSingleView(180, anime, embed, interaction.guild, interaction, self)
        else:
            view = CommentListView(180, anime, embed, interaction.guild, interaction, self)

        self.comment_children[anime.title] = view

        await interaction.response.send_message(embed=embed, view=view)

        message = await interaction.original_response()
        view.message = message

        self.viewing_comments.append(anime.title)
        
        await view.wait()

class CommentSingleView(AnimeView):
    anime: Anime
    comment: AnimeComment
    message: discord.Message
    embed: discord.Embed
    guild: discord.Guild
    interaction: discord.Interaction
    parent: AnimeView

    def __init__(self, timeout, anime: Anime, embed, guild, interaction, parent):
        super().__init__(timeout=180 if timeout is None else timeout)
        self.value = None
        self.anime = anime
        self.comment = anime.comments[0]
        self.message = None
        self.embed = embed
        self.guild = guild
        self.interaction = interaction
        self.parent = parent

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    async def update(self):
        new_embed = get_comment_embed(self.anime, self.comment, 1, len(self.anime.comments), self.guild, self.interaction)
        new_view = CommentListView(self.timeout, self.anime, new_embed, self.guild, self.interaction, self.parent)
        new_view.message = self.message

        await self.message.edit(embed=new_embed, view=new_view)
        if self.parent is not None:
            await self.parent.update()
        await new_view.wait()

    @discord.ui.button(label="Add Comment", style=discord.ButtonStyle.grey, row=4)
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(self.anime, self))

class CommentListView(AnimeView):
    anime: Anime
    message: discord.Message
    embed: discord.Embed
    guild: discord.Guild
    interaction: discord.Interaction
    parent: AnimeView

    def __init__(self, timeout, anime: Anime, embed, guild, interaction, parent):
        super().__init__(timeout=180 if timeout is None else timeout)
        self.value = None
        self.anime = anime
        self.current_index = 0
        self.message = None
        self.embed = embed
        self.guild = guild
        self.interaction = interaction
        self.parent = parent

        if len(anime.comments) == 1:
            for item in self.children:
                item.disabled = True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    async def update(self):
        self.embed = get_comment_embed(self.anime, self.anime.comments[self.current_index], self.current_index + 1, len(self.anime.comments), self.guild, self.interaction)
        await self.message.edit(embed=self.embed, view=self)
        await self.parent.update()
    
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.grey, row=3)
    async def full_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(-100, interaction)
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.grey, row=2)
    async def page_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(-5, interaction)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.grey, row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(-1, interaction)
        
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.grey, row=1)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(1, interaction)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.grey, row=2)
    async def page_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(5, interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.grey, row=3)
    async def full_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(100, interaction)

    async def change_page(self, amount: int, interaction: discord.Interaction):
        self.current_index += amount
        if amount == -100:
            self.current_index = 0
        elif amount == 100:
            self.current_index = len(self.anime.comments) - 1

        self.current_index = max(0, min(self.current_index, len(self.anime.comments) - 1))
        
        self.embed = get_comment_embed(self.anime, self.anime.comments[self.current_index], self.current_index + 1, len(self.anime.comments), self.guild, interaction)
        await interaction.response.edit_message(view=self, embed=self.embed)

    @discord.ui.button(label="Add Comment", style=discord.ButtonStyle.grey, row=4)
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(self.anime, self))

class CommentModal(discord.ui.Modal):
    text = discord.ui.TextInput(label="Comment", placeholder="Share your thoughts...", style=discord.TextStyle.long, max_length=512, required=True)
    anime: Anime
    view: AnimeView

    def __init__(self, anime, view):
        super().__init__(title=anime.title[:45])
        self.text.placeholder = f"Share your thoughts on {anime.title}"
        self.anime = anime
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.anime.add_comment(self.text.value, interaction.user.id)
        saveAnimeLists(data.instance.anime_lists)
        await interaction.response.send_message("Comment added :)", ephemeral=True)
        if is_comment_parent(self.view):
            await self.view.update_children()
        await self.view.update()

def get_anime_embed(anime: Anime, index, list_length, guild: discord.Guild) -> discord.Embed:
    color = discord.Colour.blurple()
    embed = discord.Embed(title=anime.title, color=color, description=f"**Status**\n{anime.status}")
    
    embed.add_field(name="Date Added", value=f"{anime.added_at.strftime('%m-%d-%Y')}")
    embed.add_field(name="", value="      ")
    embed.add_field(name="Last Updated", value=f"{anime.updated_at.strftime('%m-%d-%Y %H:%M:%S')}")

    if index is not None:
        embed.add_field(name="", value=f"{index} / {list_length}\n", inline=False)

    adder : discord.Member = guild.get_member(anime.added_by)

    if adder is not None:
        embed.set_footer(icon_url=adder.avatar.url, text=f'''added by {adder.name}{"" if not anime.has_comments() else f" | {len(anime.comments)} comment{'s' if len(anime.comments) > 1 else ''}"}''')

    return embed

def get_comment_embed(anime: Anime, comment: AnimeComment, index: int, list_length: int, guild: discord.Guild, interaction: discord.Interaction):
    adder : discord.Member = guild.get_member(comment.added_by)

    color = discord.Colour.fuchsia()
    embed = discord.Embed(color=color, description=comment.content, timestamp=comment.added_at)
    embed.set_author(name=adder.name if adder is not None else "user unknown", icon_url=adder.avatar.url)

    if index is not None:
        embed.add_field(name="", value=f"{index} / {list_length}\n", inline=False)

    embed.set_footer(icon_url=interaction.client.user.avatar.url if interaction is not None else None, text=anime.title)

    return embed

def is_comment_parent(view: AnimeView):
    return type(view) is RandomView or type(view) is SingleView or type(view) is ListView
