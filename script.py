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
random_player = playrandom.Player()

try:
    # import visuallogger
    # logger = visuallogger.Logger()
    xbmcaddon.Addon('script.design.helper')
    logger_installed = True
except:
    # logger = None
    logger_installed = False

LIMIT = 100
tvshow_titles_path = "videodb://tvshows/titles/" # Frig. This can also not end with a slash /

def log(message, level=xbmc.LOGDEBUG, log_to_gui=True):
    if logger_installed:
        # Yeah, this is ugly, so def want it to be a module
        builtin = 'RunScript(script.design.helper, log, %s, "%s"' % (__addonid__, message)
        if log_to_gui:
            builtin += ', logToGui'
        builtin += ')'
        xbmc.executebuiltin(builtin.encode('utf-8'))
    else:
        xbmc.log('[%s] %s' % (__addonid__, message.encode('utf-8')), level)

def main():
    if len(sys.argv) == 1:
        log("Play Random Items: 'RunScript(script.playrandom, \"(Container, ListItem).FolderPath\")'")
        return
    # TODO: Show a loading indicator
    # sys.argv[0] is script name
    full_url = sys.argv[1].decode("utf-8")
    random_player.play_random_from_full_url(full_url)

if __name__ == '__main__':
    main()
