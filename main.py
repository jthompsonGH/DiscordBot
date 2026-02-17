import discord
import asyncio
import os
import sys
import globals
from dotenv import load_dotenv
from discord.ext import commands
from cogs.timestamps import timestamp_if_valid

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True

class Discord_Bot(commands.Bot):
    def __init__(self, intents):
        super().__init__(intents=intents, command_prefix='_')

    async def on_message(self, message: discord.Message):
        print(f"{message.author.name}: \n    {message.content}")

        if (message.author.bot):
            return
        
        await timestamp_if_valid(message)
    
        msg = message.content.lower()

        if msg == 'bot help':
            await message.channel.send("We slash commands now! Start a message with **/** and look for my commands to get crackin")
            return
    
client = Discord_Bot(intents)

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != "__init__.py":
            await client.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await load()

    arg1 = None
    if len(sys.argv) > 1:
        arg1 = sys.argv[1].lower()

    if arg1 != 'prod' and arg1 != 'dev':
        print("Please supply an argument for which flavor to run: PROD or DEV")
        sys.exit(0)

    prod_token = os.environ.get('TOKEN')
    dev_token = os.environ.get('DEV_TOKEN')

    is_dev = arg1 == 'dev'
    globals.is_dev = is_dev

    token = dev_token if is_dev else prod_token

    await client.start(token)

asyncio.run(main())