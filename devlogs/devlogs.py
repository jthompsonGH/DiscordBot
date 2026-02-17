import json
import discord
import typing
from datetime import datetime
from globals import getDevString

class Devlog():
    text : str
    created_at : datetime

    def __init__(self, text, created_at):
        self.text = text
        self.created_at = created_at

    def fromJSON(dict):
        return Devlog(text=dict['text'], created_at=datetime.fromisoformat(dict['created_at']))
    
    def toJSON(self):
        dict = {
            'text': self.text,
            'created_at': self.created_at.isoformat()
        }
        return dict
    
class DevlogList():
    title : str
    logs : typing.List[Devlog]

    def __init__(self, title, logs):
        self.title = title
        self.logs = logs

    def fromJSON(dict):
        logs = []
        for log in dict['logs']:
            logs.append(Devlog.fromJSON(log))
            
        logs.sort(key= lambda log: log.created_at)
        return DevlogList(title=dict['title'], logs=logs)
    
    def toJSON(self):
        logs_jsons = []
        for l in self.logs:
            logs_jsons.append(l.toJSON())
        dict = {
            'title': self.title,
            'logs': logs_jsons
        }
        return dict
    
    def append(self, log: Devlog):
        self.logs.append(log)
        self.logs.sort(key= lambda log: log.created_at)

    
class DevlogModal(discord.ui.Modal):
    text = discord.ui.TextInput(label="Content", placeholder="Today I...", style=discord.TextStyle.long, max_length=1024, required=True)
    created_at : datetime
    list_title : str
    lists_list : typing.List[DevlogList]

    def __init__(self, lists_list, title):
        now = datetime.now()
        super().__init__(title=f"{title} Devlog: {now.strftime('%m-%d-%Y')}")
        self.created_at = now
        self.lists_list = lists_list
        self.list_title = title

    async def on_submit(self, interaction: discord.Interaction):
        new_devlog = Devlog(text=self.text.value, created_at=self.created_at)

        devlog_list = None
        for l in self.lists_list:
            if l.title.lower() == self.list_title.lower():
                devlog_list = l

        if devlog_list is None:
            devlog_list = DevlogList(title=self.list_title, logs=[])
            self.lists_list.append(devlog_list)

        devlog_list.append(new_devlog)

        saveDevlogs(self.lists_list)

        await interaction.response.send_message("Devlog added :)", ephemeral=True)

def loadDevlogs() -> typing.List[DevlogList]:
    devlog_lists = []
    try:
        with open("devlogs" + getDevString() + ".json", "r") as json_file:
            log_dicts = json.load(json_file)
            for log in log_dicts:
                devlog_lists.append(DevlogList.fromJSON(log))
            return devlog_lists
    except FileNotFoundError as e:
        print("Could not find devlogs file. Continuing as if it doesn't exist :)")
        return devlog_lists
    except Exception as e:
        raise(e)

def saveDevlogs(lists: typing.List[DevlogList]):
    json_objects = []
    try:
        for log_list in lists:
            json_objects.append(log_list.toJSON())
        with open("devlogs" + getDevString() + ".json", "w") as json_file:
            formatted_json = json.dumps(json_objects, indent=4)
            json_file.write(formatted_json)
    except Exception as e:
        print("Could not save devlogs! Error: " + str(e))

def backupDevlogLists(lists: typing.List[DevlogList]):
    json_objects = []
    try:
        for log_list in lists:
            json_objects.append(log_list.toJSON())
        with open("devlogs_backup" + getDevString() + ".json", "w") as json_file:
            formatted_json = json.dumps(json_objects, indent=4)
            json_file.write(formatted_json)
        return "Devlogs backed up!"
    except Exception as e:
        return "Failed to backup logs! Error: " + str(e)