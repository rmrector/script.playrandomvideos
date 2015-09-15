import re
import xbmc
import xbmcgui

import pykodi

from random import shuffle
from pykodi import log

def _play_videos(items):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    for item in items:
        playlist.add(item.get('file'), xbmcgui.ListItem(item.get('label')))
    xbmc.Player().play(playlist)

class RandomPlayer(object):
    def __init__(self, limit=1):
        self.limit_length = limit

    def play_randomvideos_from_path(self, path):
        xbmc.executebuiltin('ActivateWindow(busydialog)')
        videos = None
        if path['type'] == 'library':
            if path['path'][1] == 'inprogressshows.xml':
                videos = self._get_randomepisodes_by_category(showfilter={'field': 'inprogress', 'operator':'true', 'value':''})
            elif path['path'][1] == 'tvshows':
                videos = self._get_randomepisodes()
            elif path['path'][1] == 'movies':
                videos = self._get_randomvideos_from_path('library://video/movies/titles.xml/')
            elif path['path'][1] == 'musicvideos':
                videos = self._get_randomvideos_from_path('library://video/musicvideos/titles.xml/')
            elif path['path'][1] in ('files.xml', 'addons.xml'): # Trying to descend into these is probably not a good idea ever
                videos = []
        elif path['type'] == 'videodb':
            if path['path'][0] == 'tvshows':
                videos = self._get_randomepisodes_by_path(path)

        if videos == None:
            videos = self._get_randomvideos_from_path(path['full path'])

        shuffle(videos)
        _play_videos(videos)
        xbmc.executebuiltin('Dialog.Close(busydialog)')

    def _get_randomepisodes_by_path(self, path):
        path_len = len(path['path'])
        category = path['path'][1] if path_len > 1 else None
        if category in [None, 'titles']:
            tvshow_id = path['path'][2] if path_len > 2 else None
            season = path['path'][3] if path_len > 3 else None
            return self._get_randomepisodes(tvshow_id, season)
        else: # genres/years/actors/studios/tags
            if path_len == 3:
                category_id = path['path'][2]
                return self._get_randomepisodes_by_category(category, category_id, path['label'])
            else: # Nested TV show selected
                tvshow_id = path['path'][3] if path_len > 2 else None
                season = path['path'][4] if path_len > 3 else None
                return self._get_randomepisodes(tvshow_id, season)

    def _get_randomepisodes(self, tvshow_id=None, season=None):
        json_request = pykodi.get_base_json_request('VideoLibrary.GetEpisodes')
        json_request['params']['sort'] = {'method': 'random'}
        json_request['params']['limits'] = {'end': self.limit_length}
        json_request['params']['properties'] = ['file']

        if tvshow_id:
            json_request['params']['tvshowid'] = int(tvshow_id)
            if season and not season == '-1':
                json_request['params']['season'] = int(season)

        json_result = pykodi.execute_jsonrpc(json_request)
        if 'result' in json_result and 'episodes' in json_result['result']:
            return json_result['result']['episodes']
        else:
            log(json_result, xbmc.LOGWARNING)
            return []

    category_lookup = {
        'genres': 'genreid',
        'years': 'year',
        'actors': 'actor',
        'studios': 'studio',
        'tags': 'tag'}

    def _get_randomepisodes_by_category(self, category=None, category_id=None, category_label=None, showfilter=None):
        json_request = pykodi.get_base_json_request('VideoLibrary.GetTVShows')
        json_request['params']['sort'] = {'method': 'random'}
        json_request['params']['limits'] = {'end': self.limit_length}
        json_request['params']['properties'] = ['file']

        if showfilter:
            json_request['params']['filter'] = showfilter
        else:
            category = self.category_lookup.get(category, category)
            if category == 'genreid' or category == 'year':
                category_value = int(category_id)
            elif category_label:
                category_value = category_label
            json_request['params']['filter'] = {category: category_value}

        json_result = pykodi.execute_jsonrpc(json_request)
        if 'result' in json_result and 'tvshows' in json_result['result']:
            random_episodes = []
            for show in json_result['result']['tvshows']:
                random_episodes.extend(self._get_randomepisodes(show['tvshowid']))
            shuffle(random_episodes)
            return random_episodes[:self.limit_length]
        else:
            log(json_result, xbmc.LOGWARNING)
            return []

    def _get_randomvideos_from_path(self, fullpath):
        """Hits the filesystem more often than it needs to for some library paths, but it pretty much works for everything."""
        return self._recurse_randomvideos_from_path(fullpath)

    skip_foldernames = ('extrafanart', 'extrathumbs')
    plugin_recurse_blacklist = (
        'plugin://plugin.video.youtube/sign/in/',
        'plugin://plugin.video.youtube/sign/out/',
        'plugin://plugin.video.youtube/kodion/search/input/',
        'plugin://plugin.video.gametrailerscom/search/',
        'plugin://plugin.video.reddit_tv/?url=all&mode=searchVideos&type=',
        'plugin://plugin.video.reddit_tv/?url=&mode=addSubreddit&type=',
        'plugin://plugin.video.reddit_tv/?url=&mode=searchReddits&type=',
        'plugin://plugin.video.time_com/?url=&mode=search')
    plugin_recurse_blacklist_regex = (
        r'.*mode=autoPlay.*', # Reddit videos
        r'plugin://plugin\.video\.southpark_unofficial/\?url=Search&mode=list&title=Search.*icon\.png')
    def _recurse_randomvideos_from_path(self, fullpath, depth=3):
        if fullpath.startswith('plugin://'): # Traversing plugins is time consuming even on speedy hardware, limit depth to keep the delay reasonable
            depth = min(depth, 1)
        json_request = pykodi.get_base_json_request('Files.GetDirectory')
        json_request['params'] = {'directory': fullpath, 'media': 'video'}
        json_request['params']['sort'] = {'method': 'random'}
        json_request['params']['limits'] = {'end': self.limit_length * 2}

        json_result = pykodi.execute_jsonrpc(json_request)
        if 'result' in json_result and 'files' in json_result['result']:
            result = []
            for result_file in json_result['result']['files']:
                if result_file['file'].endswith(('.m3u', '.pls', '.cue')):
                    # m3u acts as a directory but "'media': 'video'" doesn't filter out flac/mp3/etc like real directories; the others probably do the same.
                    continue
                if result_file['file'].startswith('plugin://'):
                    if result_file['file'] in self.plugin_recurse_blacklist:
                        continue
                    if any(re.match(blackrg, result_file['file']) for blackrg in self.plugin_recurse_blacklist_regex):
                        continue
                if result_file['label'] in self.skip_foldernames:
                    continue
                if result_file['filetype'] == 'directory':
                    if depth > 0:
                        result.extend(self._recurse_randomvideos_from_path(result_file['file'], depth - 1))
                else:
                    result.append(result_file)

            shuffle(result)
            return result[:self.limit_length]
        else:
            log(json_result, xbmc.LOGWARNING)
            return []
