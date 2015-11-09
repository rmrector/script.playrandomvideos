import os
import sys
import urlparse
import xbmc
import xbmcaddon

addon = xbmcaddon.Addon()
resourcelibs = xbmc.translatePath(addon.getAddonInfo('path')).decode('utf-8')
resourcelibs = os.path.join(resourcelibs, u'resources', u'lib')
sys.path.append(resourcelibs)

import playrandom

from pykodi import log

ignoredtypes = ('', 'addons', 'sources', 'plugin')

def main():
    if len(sys.argv) < 2:
        log("""Play Random Videos: 'RunScript(script.playrandomvideos, \"list path\", \"label=Cartoon Network\", [limit=1], [forcewatchmode=watched])'
List path is the path to the list to play, like ListItem.FolderPath, which should be escaped ($ESCINFO[]) or wrapped in
quotation marks. 'label' is the list name, like ListItem.Label, and is required for TV Show actor/studio/tag lists, but
should always be passed in when available, also escaped/quoted. 'limit' is the number of videos to queue up, and
defaults to a single video. 'forcewatchmode' overrides the default watch mode selected in the add-on settings.""",
            xbmc.LOGNOTICE)
        xbmc.executebuiltin("Notification(See log for usage: script.playrandomvideos, RunScript(script.playrandomvideos, \"list path\", label=\"Cartoon Network\", [limit=1], [forcewatchmode=watched]), 10000)")
        return
    if not sys.argv[1]:
        return

    pathinfo = get_pathinfo()
    if pathinfo['type'] in ignoredtypes:
        return
    limit = int(pathinfo.get('limit', 1))
    randomplayer = playrandom.RandomPlayer(limit)
    randomplayer.play_randomvideos_from_path(pathinfo)

def get_pathinfo():
    pathinfo = {}
    for i in range(2, len(sys.argv)):
        arg = sys.argv[i].split("=", 1)
        pathinfo[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    pathinfo['full path'] = sys.argv[1]

    path_type, db_path = pathinfo['full path'].split('://')
    db_path = db_path.split('?', 1)
    query = urlparse.parse_qs(db_path[1]) if len(db_path) > 1 else None
    db_path = db_path[0].rstrip('/').split('/')

    pathinfo['path'] = db_path
    pathinfo['type'] = path_type
    pathinfo['query'] = query

    return pathinfo

if __name__ == '__main__':
    main()
