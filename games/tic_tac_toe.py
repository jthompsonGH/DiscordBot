import discord
import typing

# short for TicTacToeButtonState
class TBS():
    EMOTE_STRINGS = ["🟦", "❌", "⭕"]

    OPEN = 0
    X = 1
    O = 2

class TTTButton(discord.ui.Button):
    coord: int
    state: TBS

    def __init__(self, style, row, coord, parent):
        super().__init__(label=str(coord), style=style, row=row)
        self.coord = coord
        self.parent = parent
        self.state = TBS.OPEN

    async def callback(self, interaction:discord.Interaction):
        if interaction.user != self.parent.player1 and interaction.user != self.parent.player2:
            await interaction.response.send_message("You are not a player in this game!", ephemeral=True)
            return
        
        if interaction.user != self.parent.current_player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        if self.state != TBS.OPEN:
            await interaction.response.send_message("This square has already been played on.", ephemeral=True)
            return

        if interaction.user == self.parent.player1:
            self.state = TBS.X
        elif interaction.user == self.parent.player2:
            self.state = TBS.O
            
        self.disabled = True
        await self.parent.set_state(interaction, self)


class TicTacToe(discord.ui.View):
    player1: discord.User
    player2: discord.User
    current_player: discord.User
    winning_player: discord.User = None
    message: discord.Message
    buttons: typing.List[TTTButton]

    def __init__(self, timeout, player1, player2):
        super().__init__(timeout=timeout)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.buttons = []

        for i in range(9):
            row = int(i / 3) + 1
            new_button = TTTButton(style=discord.ButtonStyle.primary, row=row, coord=i + 1, parent=self)
            self.buttons.append(new_button)
            self.add_item(new_button)
        
    async def send_messages(self, interaction: discord.Interaction):
        self.message = await interaction.channel.send(getGridMessage(self), embed=getEmbed(self), view=self)
    
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(content=getGridMessage(self), embed=getEmbed(self, is_timeout=True), view=None)

    async def set_state(self, interaction: discord.Interaction, button: TTTButton):
        game_over = getVictor(self, button)
        
        no_buttons = game_over or self.current_player is None
        
        if no_buttons:
            for item in self.children:
                item.disabled = True
            self.stop()
        else:
            if self.current_player == self.player1:
                self.current_player = self.player2
            else:
                self.current_player = self.player1
        
        new_embed = getEmbed(self)

        await interaction.response.edit_message(content=getGridMessage(self), embed=new_embed, view=(self if not no_buttons else None))
        self.message = await interaction.original_response()

row_end_coords = [3, 6, 9]

def getGridMessage(ttt: TicTacToe) -> str:
    message = ""
    for i in range(len(ttt.buttons)):
        this_message = ""
        button = ttt.buttons[i]
        end_of_row = False
        if button.coord in row_end_coords:
            end_of_row = True
        this_message = f"{TBS.EMOTE_STRINGS[button.state]}"
        if end_of_row:
            this_message = this_message + "\n"
        message = message + this_message
    
    return message

def getEmbed(ttt:TicTacToe, is_timeout: bool = False) -> discord.Embed:
    description: str
    if ttt.winning_player is not None:
        description = f"{ttt.winning_player} won!"
    elif ttt.winning_player is None:
        if ttt.current_player is None:
            description = "It's a draw!"
        else:
            description = f"It's {ttt.current_player}'s turn..."
            if is_timeout:
                description = "timed out 🫡"


    embed = discord.Embed(title=f"{ttt.player1.name}   vs   {ttt.player2.name}", color=discord.Color.dark_red(), description=description)

    return embed

def getVictor(ttt:TicTacToe, button:TTTButton) -> bool:
    state = button.state
    won = False
    
    vert_lines = [[ttt.buttons[0], ttt.buttons[3], ttt.buttons[6]], [ttt.buttons[1], ttt.buttons[4], ttt.buttons[7]], [ttt.buttons[2], ttt.buttons[5], ttt.buttons[8]]]
    horiz_lines = [[ttt.buttons[0], ttt.buttons[1], ttt.buttons[2]], [ttt.buttons[3], ttt.buttons[4], ttt.buttons[5]], [ttt.buttons[6], ttt.buttons[7], ttt.buttons[8]]]
    diag_lines = [[ttt.buttons[0], ttt.buttons[4], ttt.buttons[8]], [ttt.buttons[2], ttt.buttons[4], ttt.buttons[6]]]

    all_options = [vert_lines, horiz_lines, diag_lines]
    for options in all_options:
        for o in options:
            if won:
                break
            count = 0
            for oo in o:
                if oo.state == state:
                    count += 1
            if count == 3:
                won = True
    if won:
        ttt.winning_player = ttt.current_player

    empty_squares = 0
    for button in ttt.buttons:
        if button.state == TBS.OPEN:
            empty_squares += 1

    if empty_squares == 0:
        ttt.current_player = None
    
    return won