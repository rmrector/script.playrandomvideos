from os.path import basename
from collections import deque
from random import shuffle

import quickjson
from pykodi import log, datetime_now

WATCHMODE_UNWATCHED = 'unwatched'
WATCHMODE_WATCHED = 'watched'

def get_generator(content, info):
    if content == 'tvshows':
        return RandomFilterableJSONGenerator(lambda filters, limit:
            quickjson.get_random_episodes(info.get('tvshowid'), info.get('season'), filters, limit), info.get('filters'))
    elif content == 'movies':
        return RandomFilterableJSONGenerator(quickjson.get_random_movies, info.get('filters'))
    elif content == 'musicvideos':
        return RandomFilterableJSONGenerator(quickjson.get_random_musicvideos, info.get('filters'))
    elif content == 'other':
        return RandomJSONDirectoryGenerator(info['path'], info['watchmode'])
    else:
        log("I know nothing")
        log({'content': content, 'info': info})

class RandomFilterableJSONGenerator(object):
    def __init__(self, source_function, filters=None, loadcount=25):
        """
        Args:
            source_function: takes two parameters, a list of `filters` and `limit` count
                returns an iterable
            loadcount: the max number of items to load at one time. Should be at least 1 + the
                number of upcoming items in the playlist
        """
        self.source_function = source_function

        self.filters = [{'field': 'lastplayed', 'operator': 'lessthan', 'value': datetime_now().isoformat(' ')}]
        if filters:
            self.filters.extend(filters)
        self.limit = loadcount

        self.readylist = deque()
        self.lastresults = deque(maxlen=loadcount)

    def __iter__(self):
        return self

    def next(self):
        if not self.readylist:
            filters = list(self.filters)
            if len(self.lastresults):
                filters.append({'and': [
                    {'field': 'filename', 'operator': 'isnot', 'value': [ep for ep in self.lastresults]}
                ]})
            self.readylist.extend(self.source_function(filters, self.limit))
            if not self.readylist:
                raise StopIteration()
        result = self.readylist.popleft()
        self.lastresults.append(basename(result['file']))
        return result

DIRCOUNT_WARNING = 8
DIRCOUNT_WARNING_LIMIT_SIBLINGS = 4
RECURSE_LIMIT = 3
MAX_SIBLING_FILES = 2

class RandomJSONDirectoryGenerator(object):
    def __init__(self, path, watchmode, loadcount=30):
        self.path = path
        self.watchmode = watchmode
        self.limit = loadcount
        self.dircount = 0

        self.readylist = deque()
        self.lastresults = deque(maxlen=loadcount)
        self.started = datetime_now().isoformat(' ')

    def __iter__(self):
        return self

    def next(self):
        if not self.readylist:
            self.readylist.extend(self.get_random())
            self.dircount = 0
            if not self.readylist:
                raise StopIteration()
        result = self.readylist.popleft()
        self.lastresults.append(result['file'])
        return result

    @property
    def filewarning(self):
        return self.dircount > DIRCOUNT_WARNING

    def get_random(self):
        result = self._recurse_random_from_path(self.path)
        shuffle(result)
        return result

    skip_foldernames = ('extrafanart', 'extrathumbs')
    def _recurse_random_from_path(self, fullpath, depth=RECURSE_LIMIT, check_mimetype=False):
        self.dircount += 1

        files = quickjson.get_directory(fullpath, self.limit)
        result = []
        warning_limit_siblings = 0
        sibling_files = 0
        for result_file in files:
            if result_file['filetype'] == 'directory':
                if result_file['label'] in self.skip_foldernames:
                    continue
                next_depth = depth
                if self.filewarning:
                    next_depth -= 1
                    warning_limit_siblings += 1
                if next_depth > 0 and warning_limit_siblings <= DIRCOUNT_WARNING_LIMIT_SIBLINGS:
                    next_check_mimetype = result_file['file'].endswith(('.m3u', '.pls', '.cue'))
                    result.extend(self._recurse_random_from_path(result_file['file'], next_depth - 1, next_check_mimetype))
            else:
                if check_mimetype and not result_file['mimetype'].startswith(('video', 'audio')):
                    continue
                if result_file.get('lastplayed') > self.started:
                    continue
                if result_file['file'] in self.lastresults:
                    continue
                if self.watchmode == WATCHMODE_UNWATCHED and result_file['playcount'] > 0:
                    continue
                if self.watchmode == WATCHMODE_WATCHED and result_file['playcount'] == 0:
                    continue
                if depth < RECURSE_LIMIT:
                    # Limit sibling files when we're not in the top directory
                    sibling_files += 1
                    if sibling_files > MAX_SIBLING_FILES:
                        continue
                result.append(result_file)

        return result
