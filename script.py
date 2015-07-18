from __future__ import unicode_literals

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

import xbmc

import xml.etree.ElementTree as ET

from devhelper import pykodi
from devhelper.pykodi import log

addon = pykodi.Addon()

sys.path.append(addon.resources_lib)

from playrandom import RandomPlayer
random_player = RandomPlayer()

def main():
    if len(sys.argv) == 1:
        log("Play Random Items: 'RunScript(script.playrandom, \"(Container, ListItem).FolderPath\", [video/music/pictures])'", xbmc.LOGWARNING, True)
        return
    # TODO: Show a loading indicator

    full_url = sys.argv[1].decode("utf-8")
    if len(sys.argv) > 2:
        random_player.play_random_from_full_url(full_url, sys.argv[2].decode('utf-8'))
    else:
        random_player.play_random_from_full_url(full_url)

if __name__ == '__main__':
    main()
