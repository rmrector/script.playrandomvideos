import json
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import xml.etree.ElementTree as ET

try:
    # import visuallogger
    # logger = visuallogger.Logger()
    xbmcaddon.Addon('script.design.helper')
    loggerInstalled = True
except:
    # logger = None
    loggerInstalled = False

__addonid__ = 'script.playrandom'


def log(message, level=xbmc.LOGDEBUG, logToGui=True):
    if loggerInstalled:
        # Yeah, this is ugly, so def want it to be a module
        builtin = 'RunScript(script.design.helper, log, %s, "%s"' % (__addonid__, message)
        if logToGui:
            builtin += ', logToGui'
        builtin += ')'
        xbmc.executebuiltin(builtin)
    else:
        xbmc.log('[%s] %s' % (__addonid__, message), level)


class Player:
    def __init__(self):
        self.playlistLimitLength = 100
        # special should probably be handled by a file handler or whatever
        self.videoDatabasePrefix = "videodb://"
        self.playlistSuffix = ".xsp"
        self.tvshowLibrary = 'tvshows'


    def playRandomFromFullUrl(self, path):
        if path.startswith(self.videoDatabasePrefix):
            self._playRandomFromVideoDb(path)
        elif path.endswith(self.playlistSuffix):
            self._playRandomFromPlaylist(path)
        else:
            log("Unsupported path %s" % path, xbmc.LOGNOTICE)


    def _playRandomFromVideoDb(self, path):
        # Hey, maybe I could turn this into a dictionary
        dbPath = path[len(self.videoDatabasePrefix):].split("?", 1)
        query = urllib.unquote(dbPath[1]) if len(dbPath) > 1 else None
        dbPath = dbPath[0].rstrip('/').split('/')

        pathLen = len(dbPath)
        if pathLen < 1: # Just "videodb://"
            log("Unsupported Video DB path '%s'. Investigate if there is a query." % path, xbmc.LOGNOTICE)
            return
        library = dbPath[0] # movies/tvshows/musicvideos, annoyingly also recentlyadded(movies, episodes, musicvideos)

        category = dbPath[1] if pathLen > 1 else None
        if category == 'titles':
            categoryId = None
            _i = 2
        else:
            categoryId = dbPath[2] if pathLen > 2 else None
            _i = 3

        tvshowId = dbPath[_i] if pathLen > _i else None
        season = dbPath[_i + 1] if pathLen > (_i + 1) else None
        movieId = dbPath[_i] if pathLen > _i else None

        if library == self.tvshowLibrary:
            if not tvshowId and categoryId:
                log("Want to play episodes from '%s=%s'. But I don't know how." % (category, categoryId))
            else:
                self._playRandomTvEpisode(tvshowId, season, query)
        else:
            log("Unsupported Video DB path '%s'." % path, xbmc.LOGNOTICE)

        # From context.playrandom, which passes along ListItem.FolderPath from the context menu, dbPath and query can be goofy
        # a simple 'dbPath' like 'tvshows/titles/<tvshowid>[/<season>[/episodeid]]' is clear enough
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
        # KODI-ODD: sometimes dbPath has a slash at the end and sometimes it does not

    def _playRandomTvEpisode(self, tvshowId=None, season=None, query=None):
        method_args = "(tvshowId=%s, season=%s)" % (str(tvshowId), str(season))
        jsonRequest = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "id": 1,
            "params": {"properties": ["file"], "sort": {"method": "random"}, "limits": {"end": self.playlistLimitLength}}}

        if tvshowId:
            jsonRequest["params"]["tvshowid"] = int(tvshowId)
        if season:
            jsonRequest["params"]["season"] = int(season)

        jsonEpisodes = xbmc.executeJSONRPC(json.dumps(jsonRequest))
        jsonEpisodes = json.loads(jsonEpisodes)

        if len(jsonEpisodes["result"]["episodes"]):
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            for episode in jsonEpisodes["result"]["episodes"]:
                listItem = xbmcgui.ListItem(episode["label"])
                playlist.add(episode["file"], listItem)

            xbmc.Player().play(playlist)
            log("Successfully started playing random episodes with %s" % method_args, xbmc.LOGDEBUG)
        else:
            log("Didn't find any episodes with %s" % method_args, xbmc.LOGNOTICE)


    def _playRandomFromPlaylist(self, path):
        playlistXml = xbmcvfs.File(path, 'r')
        playlistXml = playlistXml.read()
        playlistXml = ET.fromstring(playlistXml)

        if playlistXml.tag != 'smartplaylist':
            log("Playlists other than smart playlists are not supported. '%s'" % path, xbmc.LOGNOTICE)
            return
        if 'type' not in playlistXml.attrib:
            log("Playlists without a type are not supported. '%s'" % path, xbmc.LOGNOTICE)
            return

        playlistType = playlistXml.attrib['type']

        if playlistType == 'episodes':
            self._playEpisodePlaylist(path)
        else:
            log("Unsupported playlist type '%s' for path '%s'" % (playlistType, path), xbmc.LOGNOTICE)


    def _playEpisodePlaylist(self, path):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        episodeIds = xbmcvfs.listdir(path)[1]
        for episodeId in episodeIds:
            jsonRequest = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "id": 1,
                           "params": {"episodeid": int(episodeId), "properties": ["file"]}}
            episode = json.loads(xbmc.executeJSONRPC(json.dumps(jsonRequest)))
            episode = episode["result"]["episodedetails"]
            listItem = xbmcgui.ListItem(episode["label"])
            playlist.add(episode["file"], listItem)

        playlist.shuffle()
        log("Successfully started playing random episodes from '%s'" % path, xbmc.LOGDEBUG)
        xbmc.Player().play(playlist)
