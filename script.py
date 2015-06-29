# examples of URLs I need to handle
# videodb://movies/titles/6748
# videodb://movies/genres/
# videodb://movies/directors/
# videodb://movies/directors/9788/
# smb://CUBER/Other/Apps/
# special://profile/playlists/video/Buffy.xsp
# videodb://tvshows/titles/1396/?xsp={"order":{"direction":"ascending","ignorefolders":0,"method":"sorttitle"},"type":"tvshows"}
# library://video_flat/inprogressshows.xml/
# library://video_flat/recentlyaddedmovies.xml/
# library://video_flat/recentlyaddedepisodes.xml/
# videodb://tvshows/titles/1480/2/?tvshowid=1480&xsp={"order":{"direction":"ascending","ignorefolders":0,"method":"sorttitle"},"type":"tvshows"}
# ?? Keep an eye out for this one, because the filter applies to the tvshows (from the parent container), not the episodes inside the selected tv show. videodb://tvshows/titles/1580/?filter={"rules":{"and":[{"field":"rating","operator":"between","value":["9.5","10"]}]},"type":"tvshows"}&xsp={"order":{"direction":"ascending","ignorefolders":0,"method":"sorttitle"},"type":"tvshows"}

import json
import os
import urllib
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import xml.etree.ElementTree as ET

# == add-on info
__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id').decode("utf-8")
__addonpath__ = __addon__.getAddonInfo('path').decode("utf-8")
__lib__ = xbmc.translatePath(os.path.join(__addonpath__, 'resources', 'lib')).decode("utf-8")
# ==

sys.path.append(__lib__)

import playrandom
randomPlayer = playrandom.Player()

try:
    # import visuallogger
    # logger = visuallogger.Logger()
    xbmcaddon.Addon('script.design.helper')
    loggerInstalled = True
except ExplicitException:
    # logger = None
    loggerInstalled = False

LIMIT = 100
tvshowTitlesPath = "videodb://tvshows/titles/" # Frig. This can also not end with a slash /

def log(message, logToGui=True, level=xbmc.LOGDEBUG):
    if loggerInstalled:
        # Yeah, this is ugly, so def want it to be a module
        builtin = "RunScript(script.design.helper, log, %s, \"%s\"" % (__addonid__, message)
        if logToGui:
            builtin += ', logToGui'
        builtin += ')'
        xbmc.executebuiltin(builtin)
    else:
        xbmc.log('[%s] %s' % (__addonid__, message), level)

def main():
    if len(sys.argv) == 1:
        log("Play Random Items: 'RunScript(script.playrandom, \"FolderPath\")'")
        return
    # TODO: Show a loading indicator
    # sys.argv[0] is script name
    path = sys.argv[1].decode("utf-8")
    randomPlayer.playRandomFromFolderPath(path)

if __name__ == '__main__':
    main()
