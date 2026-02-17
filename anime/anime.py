import os
import typing
import json
from datetime import datetime
from globals import getDevString

class AnimeComment:
    added_by: int
    added_at: datetime
    content: str

    def __init__(self, added_by, added_at, content):
        self.added_by = added_by
        self.added_at = datetime.fromisoformat(added_at)
        self.content = content

    def toJSON(self):
        dict = {
            'added_by': self.added_by,
            'added_at': self.added_at.isoformat(),
            'content': self.content
        }
        return dict
    
    def fromJSON(dict):
        return AnimeComment(dict['added_by'], dict['added_at'], dict['content'])


class Anime:
    added_by: int
    comments: typing.List[AnimeComment]
    
    def __init__(self, title, status, added_at, updated_at, added_by, comments):
        self.title = title
        self.status = status
        self.added_at = datetime.fromisoformat(added_at)
        self.updated_at = datetime.fromisoformat(updated_at)
        self.added_by = added_by
        self.comments = comments

    def toJSON(self):
        commentJSONs = []
        for comment in self.comments:
            commentJSONs.append(comment.toJSON())
        dict = {
            'title': self.title,
            'status': self.status,
            'added_at': self.added_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'added_by': self.added_by,
            'comments': commentJSONs
            }
        return dict

    def fromJSON(dict):
        comments = []
        if 'added_by' not in dict.keys():
            dict['added_by'] = os.environ.get("DEV_USER_ID")
        if 'comments' not in dict.keys():
            dict['comments'] = []
        for entry in dict["comments"]:
            comment = AnimeComment.fromJSON(entry)
            comments.append(comment)
        return Anime(dict['title'],
            dict['status'], dict['added_at'],
            dict['updated_at'], dict['added_by'], comments)

    def updateTitle(self, new_title):
        self.title = new_title
        self.updated_at = datetime.now()

    def updateStatus(self, new_status):
        self.status = new_status
        self.updated_at = datetime.now()

    def create(title, status, user: int):
        now = datetime.now().isoformat()
        return Anime(title, status, now, now, user, [])
    
    def has_comments(self) -> bool:
        return len(self.comments) > 0
    
    def add_comment(self, content: str, adder: int):
        comment = AnimeComment(adder, datetime.now().isoformat(), content)
        self.comments.append(comment)

    
class AnimeList:
    guild_id : int
    guild_name : str
    animes : typing.List[Anime]

    def __init__(self, guild_id, guild_name, animes):
        self.guild_id = guild_id
        self.guild_name = guild_name
        self.animes = animes

    def toJSON(self):
        animeJSONs = []
        sorted_animes = getAnimes(self.animes, 'all', None)
        for anime in sorted_animes:
            animeJSONs.append(anime.toJSON())
        dict = {
            "guild_name": self.guild_name,
            "guild_id": self.guild_id,
            "animes": animeJSONs
        }
        return dict
    
    def fromJSON(dict):
        animes = []
        for entry in dict["animes"]:
            anime = Anime.fromJSON(entry)
            animes.append(anime)
        animes = pruneAnime(animes)
        animes = getAnimes(animes, 'all', None)
            
        return AnimeList(dict["guild_id"], dict["guild_name"], animes)

def sortTitle(a: Anime):
    return a.title.lower()

def sortAdded(a: Anime):
    return a.added_at

def sortUpdated(a: Anime):
    return a.updated_at
    
def filterAnimes(anime_list: typing.List[Anime], filter_term:str, exact_match=False):
    filtered_anime = []
    for anime in anime_list:
        if exact_match:
            if filter_term.lower() == anime.title.lower():
                filtered_anime.append(anime)
        else:
            if filter_term.lower() in anime.title.lower():
                filtered_anime.append(anime)
    return filtered_anime

def getAnimes(shows: typing.List[Anime], status_type:str, sort_by:str):
    if status_type is None:
        status_type = 'all'
    return_list = []
    sort_key = sortTitle
    if sort_by == 'added':
        sort_key = sortAdded
    elif sort_by == 'updated':
        sort_key = sortUpdated
    watched_anime = []
    watching_anime = []
    planned_anime = []
    for anime in shows:
        if anime.status == 'watched':
            watched_anime.append(anime)
        elif anime.status == 'watching':
            watching_anime.append(anime)
        elif anime.status == 'planned':
            planned_anime.append(anime)
    if status_type == 'all':
        return_list.extend(watched_anime)
        return_list.extend(watching_anime)
        return_list.extend(planned_anime)
    elif status_type == 'watched':
        return_list = watched_anime
    elif status_type == 'watching':
        return_list = watching_anime
    elif status_type == 'planned':
        return_list = planned_anime

    return_list.sort(key=sort_key)
    
    if sort_by == 'added' or sort_by == 'updated':
        return_list.reverse()
        
    return return_list

def loadAnimeLists() -> typing.List[AnimeList]:
    anime_lists = []
    try:
        with open("animes" + getDevString() + ".json", "r") as json_file:
            server_dicts = json.load(json_file)
            for server in server_dicts:
                if 'guild_name' not in server.keys():
                    server['guild_name'] = 'Placeholder name :)'
                anime_lists.append(AnimeList.fromJSON(server))
            return anime_lists
    except FileNotFoundError as e:
        print("Could not find animes file. Continuing as if it doesn't exist :)")
        return anime_lists
    except Exception as e:
        raise(e)

def saveAnimeLists(shows: typing.List[AnimeList]):
    json_objects = []
    try:
        for anime in shows:
            json_objects.append(anime.toJSON())
        with open("animes" + getDevString() + ".json", "w") as json_file:
            formatted_json = json.dumps(json_objects, indent=4)
            json_file.write(formatted_json)
    except Exception as e:
        print("Could not save anime! Error: " + str(e))

def backupAnimeLists(shows: typing.List[AnimeList]):
    json_objects = []
    try:
        for anime in shows:
            json_objects.append(anime.toJSON())
        with open("animes_backup" + getDevString() + ".json", "w") as json_file:
            formatted_json = json.dumps(json_objects, indent=4)
            json_file.write(formatted_json)
        return "Shows backed up!"
    except Exception as e:
        return "Failed to backup shows! Error: " + str(e)

def pruneAnime(shows: typing.List[Anime]):
    for anime in shows:
        title = anime.title
        occurrances = 0
        for show in shows:
            if show.title == title:
                occurrances += 1
        if occurrances > 1:
            print(f"{title} was duplicated. Removing")
            shows.remove(show)
    return shows
