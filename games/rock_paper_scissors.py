import discord

class Option():
    ROCK = 1
    PAPER = 2
    SCISSORS = 0

EMOTE_STRINGS = ["✂️", "🪨", "📰"]

class RockPaperScissors(discord.ui.View):
    message: discord.Message
    player1: discord.User
    player2: discord.User
    embed: discord.Embed

    player1_choice: int
    player2_choice: int

    player1_score: int
    player2_score: int

    result: str = None
    
    def __init__(self, player1, player2, timeout):
        super().__init__(timeout=timeout)
        self.player1 = player1
        self.player2 = player2
        self.player1_choice = None
        self.player2_choice = None
        self.player1_score = 0
        self.player2_score = 0

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(embed=self.embed, view=self)

    @discord.ui.button(label=EMOTE_STRINGS[Option.SCISSORS], style=discord.ButtonStyle.primary)
    async def play_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        pressed_user = interaction.user

        if pressed_user != self.player1 and pressed_user != self.player2:
            await interaction.response.send_message("You are not a player in this match.", ephemeral=True)
            return
        
        if (pressed_user == self.player1 and self.player1_choice is not None) or (pressed_user == self.player2 and self.player2_choice is not None):
            await interaction.response.send_message("You have already made a choice this round!", ephemeral=True)
            return
        
        if pressed_user == self.player1:
            self.player1_choice = Option.SCISSORS
        elif pressed_user == self.player2:
            self.player2_choice = Option.SCISSORS

        await handleResponse(self, interaction)

    @discord.ui.button(label=EMOTE_STRINGS[Option.PAPER], style=discord.ButtonStyle.primary)
    async def play_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        pressed_user = interaction.user

        if pressed_user != self.player1 and pressed_user != self.player2:
            await interaction.response.send_message("You are not a player in this match.", ephemeral=True)
            return
        
        if (pressed_user == self.player1 and self.player1_choice is not None) or (pressed_user == self.player2 and self.player2_choice is not None):
            await interaction.response.send_message("You have already made a choice this round!", ephemeral=True)
            return
        
        if pressed_user == self.player1:
            self.player1_choice = Option.PAPER
        elif pressed_user == self.player2:
            self.player2_choice = Option.PAPER

        await handleResponse(self, interaction)

    @discord.ui.button(label=EMOTE_STRINGS[Option.ROCK], style=discord.ButtonStyle.primary)
    async def play_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        pressed_user = interaction.user

        if pressed_user != self.player1 and pressed_user != self.player2:
            await interaction.response.send_message("You are not a player in this match.", ephemeral=True)
            return
        
        if (pressed_user == self.player1 and self.player1_choice is not None) or (pressed_user == self.player2 and self.player2_choice is not None):
            await interaction.response.send_message("You have already made a choice this round!", ephemeral=True)
            return
        
        if pressed_user == self.player1:
            self.player1_choice = Option.ROCK
        elif pressed_user == self.player2:
            self.player2_choice = Option.ROCK

        await handleResponse(self, interaction)



async def handleResponse(view: RockPaperScissors, interaction: discord.Interaction):
    round_over = view.player1_choice is not None and view.player2_choice is not None

    if round_over:
        rst = getRPSVictor(view.player1_choice, view.player2_choice)
        if rst == -1:
            view.result = f'{view.player1.name} won!'
        elif rst == 0:
            view.result = f'Draw!'
        elif rst == 1:
            view.result = f'{view.player2.name} won!'

    new_embed = getRPSEmbed(view, round_over)
    view.embed = new_embed

    if round_over:
        for item in view.children:
            item.disabled = True
        await interaction.response.edit_message(view=view, embed=new_embed)
        return

    await interaction.response.edit_message(view=view, embed=new_embed)

def getRPSEmbed(view: RockPaperScissors, round_reveal:bool = False) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.dark_red())
    player1_value = EMOTE_STRINGS[view.player1_choice] if round_reveal else '...' if view.player1_choice is None else '✅'
    embed.add_field(name=view.player1.name, value="\n" + player1_value)

    embed.add_field(name="", value="      ")

    player2_value = EMOTE_STRINGS[view.player2_choice] if round_reveal else '...' if view.player2_choice is None else '✅'
    embed.add_field(name=view.player2.name, value="\n" + player2_value)

    if view.result is not None:
        embed.set_footer(text=view.result)

    return embed


def getRPSVictor(choice1: int, choice2:int) -> int:
    if choice1 == choice2:
        return 0
    elif choice1 == Option.SCISSORS and choice2 == Option.PAPER:
        return -1
    elif choice1 == Option.PAPER and choice2 == Option.ROCK:
        return -1
    elif choice1 == Option.ROCK and choice2 == Option.SCISSORS:
        return -1
    else:
        return 1