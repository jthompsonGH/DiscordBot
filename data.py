import typing
from anime import AnimeList, backupAnimeLists
from devlogs import DevlogList, backupDevlogLists
from shmoogle import ShmoogleList, backupShmoogleLists

class Data():
    anime_lists: typing.List[AnimeList] = []
    devlog_lists : typing.List[DevlogList] = []
    shmoogle_lists: typing.List[ShmoogleList] = []

    def doBackup(self):
        result_string = backupAnimeLists(self.anime_lists)
        result_string += f'\n{backupDevlogLists(self.devlog_lists)}'
        result_string += f'\n{backupShmoogleLists(self.shmoogle_lists)}'

        return result_string
    
instance : Data = Data()