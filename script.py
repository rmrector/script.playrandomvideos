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

# NOTE: Plugin handling is ooky! Many include "directory" items that do something other than provide a list when selected, like Youtube's Sign In/Out and Search. A blacklist of "directory"s that it shouldn't descend into is way too cumbersome to try to find and list every damn path for every damn plugin, and will simply never be complete. And then I added regex !#%!
# - Ideally Kodi would have more than just isFolder for Python ListItems, maybe like 'video, audio, image, file, script, directory', and then the 'media' param could do the filtering, as long as the add-on sets it correctly. Every plugin would have to change for this to work, but at least it would be built into Kodi.
# NOTE: Plugins also do other weird stuff that I don't know how to deal with simply:
# - Consider southpark_unofficial: the episodes are folders so that it can queue up multiple parts of the episode when selected. Can they be set to isFolder=False and still do that? If not, how could it work if Kodi expanded beyond isFolder?
# - Or GQ: this doesn't descend from the top plugin path. Kodi can't descend it properly either, with JSON-RPC method Playlist.Add recursive directory just tries to list through the top menu over and over again. It works when selecting the category in the UI, though.
#  - plugin://plugin.video.gq/?url=/genres/Fitness.js?page=1&name=Fitness&mode=GE - in from listing main plugin, doesn't descend properly
#  - plugin://plugin.video.gq/?mode=GE&name=Fitness&url=%2fgenres%2fFitness.js%3fpage%3d1 - when selecting a category, does descend  properly
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
