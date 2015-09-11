import os
import sys
import urllib
import xbmc
import xbmcaddon

addon = xbmcaddon.Addon()
resourcelibs = xbmc.translatePath(addon.getAddonInfo('path')).decode('utf-8')
resourcelibs = os.path.join(resourcelibs, u'resources', u'lib')
sys.path.append(resourcelibs)

import playrandom

from pykodi import log

ignoredtypes = ['', 'addons']

def main():
    if len(sys.argv) < 2:
        log("Play Random Videos: 'RunScript(script.playrandomvideos, \"list path\", label=Cartoon Network, [limit=1])'\nList path is the path to the list to play, like ListItem.FolderPath, which should always be wrapped in quotation marks. 'label' is the list name, like ListItem.Label, and is required for TV Show actor/studio/tag lists (for the speed!), but should always be passed in when available. 'limit' is the number of videos to queue up.", xbmc.LOGWARNING)
        xbmc.executebuiltin("Notification(Incorrect usage of script.playrandomvideos, RunScript(script.playrandomvideos, \"list path\", label=\"Cartoon Network\", [limit=1]), 10000)")
        return
    command = get_command('path')
    path = library_path(command)
    if path['type'] in ignoredtypes:
        return
    limit = int(command.get('limit', 1))
    randomplayer = playrandom.RandomPlayer(limit)
    randomplayer.play_randomvideos_from_path(path)

def get_command(first_arg_key=None):
    command = {}
    start = 2 if first_arg_key else 1
    for x in range(start, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    if first_arg_key:
        command[first_arg_key] = sys.argv[1]
    return command

def library_path(command):
    path_type, db_path = command['path'].split('://')
    db_path = db_path.split('?', 1)
    query = urllib.unquote(db_path[1]) if len(db_path) > 1 else None
    db_path = db_path[0].rstrip('/').split('/')

    return {'full path': command['path'], 'path': db_path, 'type': path_type, 'query': query, 'label': command.get('label')}

if __name__ == '__main__':
    main()
