import discord
import re
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone as t, tzinfo
from zoneinfo import ZoneInfo

class Timestamps(commands.GroupCog, group_name='timestamp', group_description='Commands to create timestamps'):
    client : commands.Bot

    def __init__(self, client):
        self.client = client

    @app_commands.command(name="relative", description="Get a relative timestamp using minutes")
    @app_commands.describe(time="Time in minutes for the timestamp. (i.e -30 for 30 minutes ago, 45 for 45 minutes from now)")
    @app_commands.describe(response="What format to respond with such as 30 minutes ago (relative) or April 30, 2026 3:00 PM (full)")
    @app_commands.choices(response=[
        app_commands.Choice(name="relative", value="relative"),
        app_commands.Choice(name="full", value="full"),
    ])
    async def relative(self, interaction: discord.Interaction, time: float, response: app_commands.Choice[str]):
        minutes : float = 0
        
        try:
            minutes = float(time)
        except ValueError:
            await interaction.response.send_message("Please provide a valid number for time in minutes.", ephemeral=True)
            return

        future_time : datetime
        
        try:
            future_time = datetime.now(t.utc) + timedelta(minutes=minutes)
        except Exception:
            await interaction.response.send_message("There was an error creating the timestamp. Please ensure the date and time values are valid.", ephemeral=True)
            return
        
        timestamp = int(future_time.timestamp())

        format = 'R' if response.value == 'relative' else 'f'

        await interaction.response.send_message(f'`<t:{timestamp}:{format}>`', ephemeral=True)

    @app_commands.command(name="explicit", description="Get a timestamp using specific details")
    @app_commands.describe(timezone="Which timezone to base the timestamp off of")
    @app_commands.choices(timezone=[
        app_commands.Choice(name="UTC", value="UTC"),
        app_commands.Choice(name="EST", value="EST"),
        app_commands.Choice(name="PST", value="PST"),
    ])
    @app_commands.describe(response="What format to respond with such as 30 minutes ago (relative) or April 30, 2026 3:00 PM (full)")
    @app_commands.choices(response=[
        app_commands.Choice(name="relative", value="relative"),
        app_commands.Choice(name="full", value="full"),
    ])
    async def explicit(self, interaction: discord.Interaction, year: app_commands.Range[int, 1], month: app_commands.Range[int, 1, 12], day: app_commands.Range[int, 1, 31], hour: app_commands.Range[int, 0, 23], minute: app_commands.Range[int, 0, 59], timezone: app_commands.Choice[str], response: app_commands.Choice[str]):
        tz : tzinfo

        if timezone.value == 'UTC':
            tz = t.utc
        elif timezone.value == 'EST':
            tz = ZoneInfo("America/New_York")
        elif timezone.value == 'PST':
            tz = ZoneInfo("America/Los_Angeles")
        else:
            await interaction.response.send_message("Invalid timezone selected.", ephemeral=True)
            return
        
        dt : datetime

        try:
            dt = datetime(year, month, day, hour, minute, tzinfo=tz)
        except:
            await interaction.response.send_message("There was an error creating the timestamp. Please ensure the date and time values are valid.", ephemeral=True)
            return

        timestamp = int(dt.timestamp())

        format = 'R' if response.value == 'relative' else 'f'

        await interaction.response.send_message(f'`<t:{timestamp}:{format}>`', ephemeral=True)

async def setup(client: commands.Bot):
    await client.add_cog(Timestamps(client))

ts_pattern = re.compile(r"(?:brb|in|give\s+me|gimme|need)(?:\s+(?:like|about|around|abt|arnd))?\s+(?:~)?(\d+(?:\.\d+)?)(?:\s*(?:~?ish))?\s*(sec|secs|min|mins|minute|minutes|hr|hrs|hour|hours)")
async def timestamp_if_valid(message: discord.Message):
    match = ts_pattern.search(message.content)
    if not match: return
    time = None
    try:
        time = float(match.group(1))
    except ValueError as e:
        print("Failed to parse value in timestamp_if_valid: " + str(e))
        return
    
    unit = match.group(2)
    ts = datetime.now(t.utc)
    delta = None
    if is_second(unit):
        delta = timedelta(seconds=time)
    elif is_minute(unit):
        delta = timedelta(minutes=time)
    elif is_hour(unit):
        delta = timedelta(hours=time)
    else:
        print("Failed to parse time unit in timestamp_if_valid: " + unit)
        return
    
    stamp = int((ts + delta).timestamp())
    ts_relative = f"<t:{stamp}:R>"
    ts_full = f"<t:{stamp}:f>"

    await message.channel.send(ts_relative)
        
def is_second(unit: str) -> bool:
            return unit.lower() in ['sec', 'secs', 'sex', 'second', 'seconds']

def is_minute(unit: str) -> bool:
            return unit.lower() in ['min', 'mins', 'minute', 'minutes']

def is_hour(unit: str) -> bool:
            return unit.lower() in ['hr', 'hrs', 'hour', 'hours']
    