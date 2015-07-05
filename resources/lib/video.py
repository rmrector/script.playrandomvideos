import xbmc
import xbmcgui

import os
import json

class Video(object):
    def __init__(self, movie_json):
        self.kodi_label = movie_json.get('label')
        self.file = movie_json.get('file')

    @property
    def listitem(self):
        """Build a Kodi ListItem that can be added to a "playlist" (Kodi play queue in python, not a real playlist) from this Movie"""
        listitem = xbmcgui.ListItem(self.label.encode('utf-8'))
        listitem.setInfo('video', {})

        return listitem

    @property
    def label(self):
        gobbledeegook_label = self.kodi_label.count('.') < 2 and self.kodi_label.count(' ') < 1
        if gobbledeegook_label:
            # Grab the containing folder name for a chance at a better label
            path = os.path.dirname(self.file)
            return path.split('/')[-1]
        else:
            return self.kodi_label
