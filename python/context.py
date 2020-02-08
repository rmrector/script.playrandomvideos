import sys
import xbmc

from lib import playrandom
from lib.pykodi import get_pathinfo

# DEPRECATED: StringCompare and SubString in addon.xml is deprecated in Krypton, gone in Leia,
#  but both options resolve to False when unrecognized so the result is the same for all versions

if __name__ == '__main__':
    path = sys.listitem.getfilename()
    label = sys.listitem.getLabel()
    watchmode = xbmc.getInfoLabel('Control.GetLabel(10)')
    if path and label:
        pathinfo = {'full path': path, 'label': label, 'watchmode': watchmode}
        pathinfo.update(get_pathinfo(path))
        playrandom.play(pathinfo)
