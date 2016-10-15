import xbmc
from os.path import basename
from collections import deque
from random import choice, shuffle
from time import time

import quickjson
from pykodi import log, datetime_now

WATCHMODE_UNWATCHED = 'unwatched'
WATCHMODE_WATCHED = 'watched'

def get_generator(content, info, singleresult):
    if content == 'tvshows':
        return RandomFilterableJSONGenerator(lambda filters, limit:
            quickjson.get_random_episodes(info.get('tvshowid'), info.get('season'), filters, limit),
            info.get('filters'), singleresult)
    elif content == 'movies':
        return RandomFilterableJSONGenerator(quickjson.get_random_movies, info.get('filters'), singleresult)
    elif content == 'musicvideos':
        return RandomFilterableJSONGenerator(quickjson.get_random_musicvideos, info.get('filters'), singleresult)
    elif content == 'other':
        return RandomJSONDirectoryGenerator(info['path'], info['watchmode'], singleresult)
    else:
        log("I don't know what to do with this:", xbmc.LOGWARNING)
        log({'content': content, 'info': info}, xbmc.LOGWARNING)

class RandomFilterableJSONGenerator(object):
    def __init__(self, source_function, filters=None, singleresult=False):
        """
        Args:
            source_function: takes two parameters, a list of `filters` and `limit` count
                returns an iterable
            filters: a list of additional filters to be passed to the source_function
        """
        self.source_function = source_function

        self.filters = [{'field': 'lastplayed', 'operator': 'lessthan', 'value': datetime_now().isoformat(' ')}]
        if filters:
            self.filters.extend(filters)
        self.singleresult = singleresult
        self.singledone = False

        self.readylist = deque()
        self.lastresults = deque(maxlen=20)

    def __iter__(self):
        return self

    def next(self):
        if self.singleresult:
            if self.singledone:
                raise StopIteration()
            else:
                self.singledone = True
        if not self.readylist:
            filters = list(self.filters)
            if len(self.lastresults):
                filters.append({'field': 'filename', 'operator': 'isnot', 'value': [ep for ep in self.lastresults]})
            self.readylist.extend(self.source_function(filters, 1 if self.singleresult else 20))
            if not self.readylist:
                raise StopIteration()
        result = self.readylist.popleft()
        self.lastresults.append(basename(result['file']))
        return result

class RandomJSONDirectoryGenerator(object):
    def __init__(self, path, watchmode, singleresult=False):
        self.path = path
        self.watchmode = watchmode
        self.singleresult = singleresult

        self.firstrun = True
        self.workcount = 0

        self.readylist = deque()
        self.unuseddirs = set()
        self.unuseddirs.add(path)
        self.unuseditems = []

    def __iter__(self):
        return self

    def next(self):
        if self.singleresult:
            if not self.firstrun:
                raise StopIteration()
        if not self.readylist:
            self.readylist.extend(self._get_random())
            if not self.readylist:
                raise StopIteration()
            self.firstrun = False
            self.workcount = 0
        else:
            self.workcount = self.workcount + 1 % 3
            if self.workcount == 0:
                self._fill_random()
        result = self.readylist.popleft()
        return result

    def _pop_randomdir(self):
        if not len(self.unuseddirs):
            return None
        result = choice(tuple(self.unuseddirs))
        self.unuseddirs.remove(result)
        return result

    def _pop_randomitem(self):
        if not self.unuseditems:
            return None
        result = choice(tuple(self.unuseditems))
        self.unuseditems.remove(result)
        return result

    def _get_random(self):
        dirs, files = self._get_next_files()
        self.unuseddirs |= dirs
        if not files: # We're out of directories and files, load up the last of the items
            shuffle(self.unuseditems)
            return self.unuseditems

        result = [choice(tuple(files))]
        files.remove(result[0])
        newitem = self._pop_randomitem()
        if newitem:
            result.append(newitem)
        self.unuseditems.extend(files)
        shuffle(result)
        return result

    def _fill_random(self):
        dirs, files = self._get_next_files()
        self.unuseddirs |= dirs
        self.unuseditems.extend(files)

    def _get_next_files(self):
        path_to_use = self._pop_randomdir()
        files = ()
        result_dirs = set()
        if not path_to_use:
            return result_dirs, files
        if self.firstrun:
            timeout = time() + 10
        while not files and path_to_use:
            log("Listing '{0}'".format(path_to_use), xbmc.LOGINFO)
            dirs, files = self._get_random_from_path(path_to_use)
            result_dirs |= dirs
            if self.firstrun and time() > timeout:
                log("Timeout reached", xbmc.LOGINFO)
                break
            if not files:
                log("No items found", xbmc.LOGINFO)
                path_to_use = self._pop_randomdir()
                if not path_to_use and result_dirs:
                    path_to_use = choice(tuple(result_dirs))
                    result_dirs.remove(path_to_use)
        return result_dirs, files

    def _get_random_from_path(self, fullpath):
        files = quickjson.get_directory(fullpath)
        result_dirs = set()
        result_files = []
        for dfile in files:
            if dfile['filetype'] == 'directory':
                result_dirs.add(dfile['file'])
            else:
                check_mimetype = fullpath.endswith(('.m3u', '.pls', '.cue'))
                if check_mimetype and not dfile['mimetype'].startswith('video'):
                    continue
                if self.watchmode == WATCHMODE_UNWATCHED and dfile['playcount'] > 0:
                    continue
                if self.watchmode == WATCHMODE_WATCHED and dfile['playcount'] == 0:
                    continue
                result_files.append(dfile)
                if self.singleresult:
                    break
        return result_dirs, result_files
