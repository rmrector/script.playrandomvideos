import json
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
except ExplicitException:
    # logger = None
    loggerInstalled = False

__addonId__ = 'script.playrandom'


def log(message, logToGui=True, level=xbmc.LOGDEBUG):
    if loggerInstalled:
        # Yeah, this is ugly, so def want it to be a module
        builtin = 'RunScript(script.design.helper, log, %s, "%s"' % (__addonId__, message)
        if logToGui:
            builtin += ', logToGui'
        builtin += ')'
        xbmc.executebuiltin(builtin)
    else:
        xbmc.log('[%s] %s' % (__addonid__, message), level)


class Player:
    def __init__(self):
        self.LIMIT = 100
        self.tvshowTitlesPath = "videodb://tvshows/titles/"


    def playRandomFromFolderPath(self, path):
        log("Looking for path: %s" % path)

        playlistExtension = ".xsp" # or .m3u, .pls
        if (path.startswith(self.tvshowTitlesPath)):
            self._playTvShow(path)
        elif(path.endswith(playlistExtension)):
            playlistXml = xbmcvfs.File(path, 'r')
            playlistXml = playlistXml.read()
            playlistXml = ET.fromstring(playlistXml)

            if playlistXml.tag != 'smartplaylist':
                log("Playlists other than smart playlists are not supported. '%s'" % path)
                return
            if 'type' not in playlistXml.attrib:
                log("A playlist without a type confuses me! '%s'" % path)
                return

            playlistType = playlistXml.attrib['type']

            if playlistType == 'episodes':
                self._playEpisodePlaylist(path)
            else:
                log("Unsupported playlist type '%s' for path '%s'" % (playlistType, playlistType))
        else:
            log("Unsupported path! %s" % path)


    def _playTvShow(self, path):
        originalPath = path
        path = path[len(self.tvshowTitlesPath):].split('?')[0].split('/')

        tvshowId = path[0]
        season = path[1] if len(path) > 1 else None

        jsonRequest = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "id": 1}
        jsonRequest["params"] = {"properties": ["file"], "sort": {"method": "random"}, "limits": {"end": self.LIMIT}}

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
            log("Successfully random'd '%s'" % originalPath)
        else:
            log("Couldn't find any episodes to random")


    def _playEpisodePlaylist(self, path):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        episodeIds = xbmcvfs.listdir(path)[1]
        for episodeId in episodeIds:
            jsonRequest = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "id": 1}
            jsonRequest["params"] = {"episodeid": int(episodeId), "properties": ["file"]}
            episode = json.loads(xbmc.executeJSONRPC(json.dumps(jsonRequest)))
            episode = episode["result"]["episodedetails"]
            listItem = xbmcgui.ListItem(episode["label"])
            playlist.add(episode["file"], listItem)

        playlist.shuffle()
        log("Successfully random'd '%s'" % path)
        xbmc.Player().play(playlist)
