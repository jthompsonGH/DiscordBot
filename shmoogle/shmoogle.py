import typing
import json
from globals import getDevString

class ShmoogleTracker():
    user_id: int
    count: int

    def __init__(self, user_id: int, count):
        self.user_id = user_id
        self.count = count if count is not None else 0

    def increment(self):
        self.count += 1

    def toJSON(self):
        dict = {
            "user": self.user_id,
            "count": self.count
        }
        return dict
    
    def fromJSON(dict):
        return ShmoogleTracker(user_id=dict['user'], count=dict['count'])

class ShmoogleList():
    guild_id: int
    guild_name: str
    trackers: typing.List[ShmoogleTracker]

    def __init__(self, guild_id, guild_name, trackers):
        self.guild_id = guild_id
        self.guild_name = guild_name
        self.trackers = trackers

    def toJSON(self):
        tracker_jsons = []
        for tracker in self.trackers:
            tracker_jsons.append(tracker.toJSON())
        dict = {
            "guild_id": self.guild_id,
            "guild_name": self.guild_name,
            "trackers": tracker_jsons
        }
        return dict
    
    def fromJSON(dict):
        trackers = []
        for t in dict['trackers']:
            trackers.append(ShmoogleTracker.fromJSON(t))
        return ShmoogleList(dict['guild_id'], dict['guild_name'], trackers)
    
    def add_tracker(self, tracker: ShmoogleTracker):
        self.trackers.append(tracker)


def loadTrackerLists() -> typing.List[ShmoogleList]:
    shmoogle_lists = []
    try:
        with open("shmoogles" + getDevString() + ".json", "r") as json_file:
            server_dicts = json.load(json_file)
            for server in server_dicts:
                if 'guild_name' not in server.keys():
                    server['guild_name'] = 'Placeholder name :)'
                shmoogle_lists.append(ShmoogleList.fromJSON(server))
            return shmoogle_lists
    except FileNotFoundError as e:
        print("Could not find shmoogles file. Continuing as if it doesn't exist :)")
        return shmoogle_lists
    except Exception as e:
        raise(e)

def saveTrackerLists(lists: typing.List[ShmoogleList]):
    json_objects = []
    try:
        for tracker in lists:
            json_objects.append(tracker.toJSON())
        with open("shmoogles" + getDevString() + ".json", "w") as json_file:
            formatted_json = json.dumps(json_objects, indent=4)
            json_file.write(formatted_json)
    except Exception as e:
        print("Could not save shmoogles! Error: " + str(e))

def backupShmoogleLists(lists: typing.List[ShmoogleList]):
    json_objects = []
    try:
        for tracker in lists:
            json_objects.append(tracker.toJSON())
        with open("shmoogles_backup" + getDevString() + ".json", "w") as json_file:
            formatted_json = json.dumps(json_objects, indent=4)
            json_file.write(formatted_json)
        return "Shmoogles backed up!"
    except Exception as e:
        return "Failed to backup shmoogles! Error: " + str(e)