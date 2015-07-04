
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import json
import urllib
import xml.etree.ElementTree as ET
from random import shuffle

from episode import Episode
from movie import Movie
# from devhelper import log

try:
    xbmcaddon.Addon('script.design.helper')
    logger_installed = True
except:
    logger_installed = False

__addonid__ = 'script.playrandom'

def log(message, level=xbmc.LOGDEBUG, log_to_gui=True):
    if logger_installed:
        # Yeah, this is ugly, so def want it to be a module
        # Also, it may choke on messages that have double-quotes and commas
        builtin = 'RunScript(script.design.helper, log, %s, "%s"' % (__addonid__, str(message).replace('"', '\''))
        if log_to_gui:
            builtin += ', log_to_gui'
        builtin += ')'
        xbmc.executebuiltin(builtin.encode('utf-8'))
    else:
        xbmc.log('[%s] %s' % (__addonid__, str(message).encode('utf-8')), level)

def library_path(path):
    db_path = path.split('://')[1].split('?', 1)
    query = urllib.unquote(db_path[1]) if len(db_path) > 1 else None
    db_path = db_path[0].rstrip('/').split('/')

    return {'db_path': db_path, 'query': query}

def wait():
    xbmc.sleep(100)

def play(playable_items):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    for playable_item in playable_items:
        playlist.add(playable_item.file, playable_item.listitem)

    xbmc.Player().play(playlist)


class Player(object):
    def __init__(self):
        self.playlist_limit_length = 5
        # special should probably be handled by a file handler or whatever
        self.video_database_prefix = 'videodb://'
        self.playlist_suffix = '.xsp'
        self.tvshow_library = 'tvshows'
        self.movie_library = 'movies'

    # I would also like to support a list of items directly, for instance if several movies are selected, a method
    #  would accept a list of the full paths to the movies, and then play those randomly. Probably even a list of
    #  container paths, that would then need to be resolved and fetched, much like tvshow/genres/<genreid>
    def play_random_from_full_url(self, path):
        # What to do with a full path directly to the item?
        if path.startswith(self.video_database_prefix):
            self._play_random_from_video_db(path)
        elif path.endswith(self.playlist_suffix):
            self._play_random_from_playlist(path)
        else:
            log("Unsupported path %s" % path, xbmc.LOGNOTICE)

        # 'Files.GetDirectory' will give me a decent list of just about every container, but it does still have some problems:
        # - It often returns a list of stuff that can't be random'd directly, like seasons, albums, or TV shows.
        #  - For lists like these, they need to be listed themselves, their contents concat'd, and then random that list
        #   - The type of info to request is also unknown until we can see what is inside of it
        #  - Or parse the path and file (if an xsp) to see what it's a list of
        #   - If it's going to be a list of items that are unplayable directly, then build a new path that describes what is wanted, if possible (if an artist is selected, add '-1' as the album to get all songs, or for a tv show set the season to '-1')
        #   - If not possible, maybe a playlist that searches for tv shows, then cache the IDs returned from GetDirectory, and build new requests to GetDirectory to ge the listing for each, add them all together and shuffle
        #   - This should also give me enough info to decide what type of info I need, episode/movie/song
        #   - But it seems like it will perform worse than 'VideoLibrary.GetEpisodes' for playing episodes from all files
        #  - Or request all of the info I would need for any type, and just ignore data that I don't need
        # - Seasons are viewed with the file as a filesystem file/directory, not a videodb:// path I can use. !! But hey, musicdb albums do have a musicdb:// path
        # - The property 'streamdetails' doesn't ever seem to be populated
        # - It ignores the query. Which is probably a good thing, since the query is built improperly anyway
        # - There is no way to limit it, so the list must be trimmed afterward

        # TV show: Lists season, including '* All seasons', but only if there is more than one season
        # - 'type' of items is Unknown
        # TV show - season: lists episodes in season. '-1' is all episodes, '0' is specials
        # - 'type' of items is episode
        # TV show - <category>: lists category IDs, 'type' is unknown
        # TV show - <category> - <category ID>: list matching TV shows, 'type' is tvshow

        # episode playlist: lists episodes in playlist
        # - 'type' of items is episode

        # "Player.Open" on any library path tries to open everything in the picture slideshow viewer, but only succeeds in grabbing a frame from a video. Maybe the first frame from the first video
        # - on a playlist it does the same thing. Doesn't work
        # - on a file folder it works, but it go through the slideshow viewer. The slideshow viewer pops up for a moment, the sees that the first item is a video so pops up the video player. In betweeen items the slideshow pops in very briefly, and when stopped, it keeps the slideshow fullscreen with a gigantic play button on it. This also means that the play queue only contains the one item that the slideshow viewer parses out to play.
        # - Just not useable


    def _play_random_from_video_db(self, path):
        _path = library_path(path)['db_path']
        if not _path:
            log("Unsupported Video DB path '%s'. Investigate if there is a query." % path, xbmc.LOGNOTICE)
        library = _path[0]
        _path = None

        if library == self.tvshow_library:
            self._play_random_tv_episodes_by_path(path)
        elif library == self.movie_library:
            self._play_random_movies_by_path(path)
        else:
            log("Unsupported Video DB path '%s'." % path, xbmc.LOGNOTICE)


    def _play_random_tv_episodes_by_path(self, path):
        db_path = library_path(path)['db_path']
        path_len = len(db_path)

        category = db_path[1] if path_len > 1 else None
        if category == 'titles':
            tvshow_id = db_path[2] if path_len > 2 else None
            season = db_path[3] if path_len > 3 else None
            # Will play from the season if an episode was passed in
            self._play_random_tv_episodes(tvshow_id, season)
        else: # genres/years/actors/studios/tags
            if path_len < 3: # No category_id
                self._play_random_tv_episodes()
            elif path_len == 3:
                categoryId = db_path[2]
                self._play_random_tv_episodes_from_category(category, categoryId)
            else:
                # With a TV show selected we just ignore the initial filter, it was only meant to filter the TV show selection
                tvshow_id = db_path[3] if path_len > 2 else None
                season = db_path[4] if path_len > 3 else None
                self._play_random_tv_episodes(tvshow_id, season)


    def _play_random_tv_episodes(self, tvshow_id=None, season=None):
        random_episodes = self._get_random_tv_episodes(tvshow_id, season)
        _method_args = "(tvshow_id=%s, season=%s)" % (str(tvshow_id), str(season))
        if random_episodes:
            play(random_episodes)
            log("Successfully started playing random episodes with %s" % _method_args, xbmc.LOGDEBUG)
        else:
            log("Didn't find any episodes with %s" % _method_args, xbmc.LOGNOTICE)


    def _play_random_tv_episodes_from_category(self, category, category_id):
        category_lookup = {
            'genres': 'genreid',
            'years': 'year',
            'actors': 'actor',
            'studios': 'studio',
            'tags': 'tag'}
        category = category_lookup[category]

        if category == 'genreid' or category == 'year':
            category_id = int(category_id)

        json_request = {'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows', 'id': 1,
            'params': {'filter':{category: category_id}}}

        json_tvshows = xbmc.executeJSONRPC(json.dumps(json_request).encode('utf-8')).decode('utf-8')
        json_tvshows = json.loads(json_tvshows)

        _method_args = "(category=%s, category_id=%s)" % (str(category), str(category_id))
        if json_tvshows['result']:
            random_episodes = [zip(*self._get_random_tv_episodes(show['tvshowid'])) for show in json_tvshows['result']['tvshows']]
            shuffle(random_episodes)
            random_episodes = random_episodes[:self.playlist_limit_length]
            play(random_episodes)
            log("Successfully started playing random episodes with %s" % _method_args, xbmc.LOGDEBUG)
        else:
            log("Didn't find any tv shows with %s" % _method_args, xbmc.LOGNOTICE)


    def _get_random_tv_episodes(self, tvshow_id=None, season=None):
        json_request = {'jsonrpc': '2.0', 'method': 'VideoLibrary.GetEpisodes', 'id': 1,
            'params': {'properties': ['file', 'title', 'season', 'episode', 'showtitle'], 'sort': {'method': 'random'}, 'limits': {'end': self.playlist_limit_length}}}

        if tvshow_id:
            json_request['params']['tvshowid'] = int(tvshow_id)
            if season and not season == '-1': # even though this param defaults to -1 for all seasons, it still chokes if passed in
                json_request['params']['season'] = int(season)

        json_episodes = xbmc.executeJSONRPC(json.dumps(json_request).encode('utf-8')).decode('utf-8')
        json_episodes = json.loads(json_episodes)

        if 'result' in json_episodes:
            return [Episode(episode) for episode in json_episodes['result']['episodes']]
        else:
            return []


    def _play_random_movies_by_path(self, path):
        # For movies I don't have to deal with many paths that can't be listed directly, so 'Files.GetDirectory' is the most straightforward option
        original_path = path
        db_path = library_path(path)['db_path']
        path_len = len(db_path)

        category = db_path[1] if path_len > 1 else None

        # Just pick from all movies if there is no movie ID or category ID
        if path_len < 3:
            path = 'videodb://movies/titles/'

        # This will fail if a movie is passed in directly, 'movies/titles/<movieid>' or 'movies/<category>/<categoryid>/<movieid>'
        json_request = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory', 'id': 1,
            'params': {'properties': ['file', 'title'], 'directory': path}}
        json_movies = json.loads(xbmc.executeJSONRPC(json.dumps(json_request).encode('utf-8')).decode('utf-8'))

        if 'result' in json_movies:
            random_movies = [Movie(movie) for movie in json_movies['result']['files']]
            shuffle(random_movies)
            random_movies = random_movies[:self.playlist_limit_length]
            play(random_movies)
            log("Successfully started playing random movies from '%s'" % original_path, xbmc.LOGDEBUG)
        else:
            log("Didn't find any movies from '%s'" % original_path, xbmc.LOGNOTICE)

    # From context.playrandom, which passes along ListItem.FolderPath from the context menu, db_path and query can be goofy
    # a simple 'db_path' like 'tvshows/titles/<tvshowid>[/<season>[/episodeid]]' is clear enough
    # - also the head of sub-sections are fine; 'tvshows/genres/<genreid>'
    # - but going deeper 'tvshows/genres/<genreid>/<tvshowid>/<season>/<episodeid>' gets a bit murky
    # - But! to turn this guy back in to what is clear, just replace 'genres/<genreid>' with 'titles'
    #  - We only really expect the genre selection to apply to the TV show itself, then list all seasons and episodes contained within
    #  - Ditto years/actors/studios/tags
    # 'query' is very icky. It looks acceptable, but it does not always accurately describe either the ListItem or its Container.
    # - Most of the time, it is simply in the reverse order of the path used to get to the Container of the ListItem, rather than the ListItem itself
    #  - The query for 'tvshows/year/<year>/<tvshowid>/<season>/<episodeid>' is 'season=<season>&tvshowid=<tvshowid>&year=<year>'
    #  - even when the selected season/episode ListItem aired in a different year, the <year> selected when navigating is displayed
    #  - even when the Container aired in a different year (or doesn't have an associated year), the year is displayed, with the wrong value
    # - Rarely it does actually describe the ListItem itself
    #  - ListItem 'movies/sets/<setid>' is the one culprit, and has a query of 'setid=<setid>'
    # - Sometimes it also includes an 'xsp' query, which is JSON that describes more of the Container's info, such as sort, filter
    #  - This seems to happen when navigating from the virtual library directory tree, rather than when accessed with a 'videodb://tvshows/titles/' URL.
    #  - A ListItem inside of a smart playlist it fully describes the rules the smart playlist is built with
    #  - In Progress TV Shows path is a nice 'tvshows/titles/<tvshowid>' and the xsp is a filter for inprogress
    # path = 'tvshows/year/<year>/<tvshowid>/<season>/<episodeid>' query = 'season=<season>&tvshowid=<tvshowid>&year=<year>' : ICK
    # KODI--: This is just... an important API with an unpleasant design
    # KODI-ODD: sometimes db_path has a slash at the end and sometimes it does not


    def _play_random_from_playlist(self, path):
        playlist_xml = xbmcvfs.File(path.encode('utf-8'), 'r')
        playlist_xml = playlist_xml.read()
        playlist_xml = ET.fromstring(playlist_xml)

        if playlist_xml.tag != 'smartplaylist':
            log("Playlists other than smart playlists are not supported. '%s'" % path, xbmc.LOGNOTICE)
            return
        if 'type' not in playlist_xml.attrib:
            log("Playlists without a type are not supported. '%s'" % path, xbmc.LOGNOTICE)
            return

        playlist_type = playlist_xml.attrib['type']
        if playlist_type == 'episodes':
            self._play_random_from_episode_playlist(path)
        elif playlist_type == 'movies':
            self._play_random_from_movie_playlist(path)
        else:
            log("Unsupported playlist type '%s' for path '%s'" % (playlist_type, path), xbmc.LOGNOTICE)


    def _play_random_from_episode_playlist(self, path):
        json_request = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory', 'id': 1,
            'params': {'properties': ['file', 'title', 'season', 'episode', 'showtitle'], 'directory': path}}
        json_episodes = json.loads(xbmc.executeJSONRPC(json.dumps(json_request).encode('utf-8')).decode('utf-8'))

        if 'result' in json_episodes:
            random_episodes = [Episode(episode) for episode in json_episodes['result']['files']]
            shuffle(random_episodes)
            random_episodes = random_episodes[:self.playlist_limit_length]
            play(random_episodes)
            log("Successfully started playing random episodes from '%s'" % path, xbmc.LOGDEBUG)
        else:
            log("Didn't find any episodes from '%s'" % path, xbmc.LOGNOTICE)


    def _play_random_from_movie_playlist(self, path):
        json_request = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory', 'id': 1,
            'params': {'properties': ['file', 'title'], 'directory': path}}
        json_movies = json.loads(xbmc.executeJSONRPC(json.dumps(json_request).encode('utf-8')).decode('utf-8'))

        if 'result' in json_movies:
            random_movies = [Movie(movie) for movie in json_movies['result']['files']]
            shuffle(random_movies)
            random_movies = random_movies[:self.playlist_limit_length]
            play(random_movies)
            log("Successfully started playing random movies from '%s'" % path, xbmc.LOGDEBUG)
        else:
            log("Didn't find any movies from '%s'" % path, xbmc.LOGNOTICE)
