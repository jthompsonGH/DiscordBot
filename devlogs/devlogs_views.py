from devlogs import Devlog, DevlogList
from discord.ext import commands
import discord

def getDevlogEmbed(log: Devlog, list_title: str, user: discord.User, index: int, list_size: int):
    embed = discord.Embed(title=f"{list_title} Devlog", color=discord.Color.gold())
    embed.add_field(name=log.created_at.strftime('%m-%d-%Y %H:%M:%S'), value=log.text)

    if index is not None:
        embed.set_footer(text=f"{index}/{list_size}")

    return embed

class DevlogView(discord.ui.View):
    list : DevlogList
    embed : discord.Embed
    message : discord.Message
    bot : commands.Bot

    def __init__(self, timeout, list, embed, bot):
        super().__init__(timeout=timeout)
        self.list = list
        self.current_index = 0
        self.message = None
        self.embed = embed
        self.bot = bot

        if len(self.list.logs) == 1:
            for item in self.children:
                item.disabled = True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)     
    
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
            self.current_index = len(self.list.logs) - 1

        self.current_index = max(0, min(self.current_index, len(self.list.logs) - 1))
        
        self.embed = getDevlogEmbed(self.list.logs[self.current_index], self.list.title, self.bot.user, self.current_index + 1, len(self.list.logs))
        await interaction.response.edit_message(embed=self.embed, view=self)

    