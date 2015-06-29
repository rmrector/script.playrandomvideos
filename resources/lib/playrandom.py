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
        self.tvshowTitlesPath = "videodb://tvshows/titles"


    def playRandomFromFolderPath(self, path):
        log("Looking for path: %s" % path)

        playlistExtension = ".xsp"
        if (path.startswith(self.tvshowTitlesPath)):
            self.playTvShow(path)
        elif(path.endswith(playlistExtension)):
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlistLoaded = False

            playlistXml = xbmcvfs.File(path, 'r')
            playlistXml = playlistXml.read()
            playlistXml = ET.fromstring(playlistXml)
            if playlistXml.tag == 'smartplaylist' and 'type' in playlistXml.attrib and playlistXml.attrib['type'] == 'episodes':
                episodeIds = xbmcvfs.listdir(path)[1]
                for episodeId in episodeIds:
                    jsonRequest = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "id": 1}
                    jsonRequest["params"] = {"episodeid": int(episodeId), "properties": ["file"]}
                    episode = json.loads(xbmc.executeJSONRPC(json.dumps(jsonRequest)))
                    episode = episode["result"]["episodedetails"]
                    listItem = xbmcgui.ListItem(episode["label"])
                    playlist.add(episode["file"], listItem)
                    print episode["label"]
                playlistLoaded = True
            else:
                log("[context.playrandom] Unsupported playlist! '%s'" % path)

            if playlistLoaded:
                playlist.shuffle()
                log("[context.playrandom] Successfully random'd '%s'" % path)
                xbmc.Player().play(playlist)
        else:
            log("[context.playrandom] Unsupported path! %s" % path)


    def playTvShow(self, path):
        originalPath = path
        path = path[len(self.tvshowTitlesPath) + 1:].split('?')[0].split('/')

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
            log("[context.playrandom] Successfully random'd '%s'" % originalPath)
        else:
            log("[context.playrandom] Couldn't find any episodes to random")
