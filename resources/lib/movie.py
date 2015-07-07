from __future__ import unicode_literals

import json
import xbmcgui

class Movie(object):
    def __init__(self, movie_json):
        self.kodi_label = movie_json.get('label')
        self.movie_id = movie_json.get('id', None)
        self.file = movie_json.get('file')
        self.title = movie_json.get('title', None)

        self.kodi_type = movie_json.get('type', None)

    @property
    def listitem(self):
        """Build a Kodi ListItem that can be added to a "playlist" (Kodi play queue in python, not a real playlist) from this Movie"""
        listitem_info = {}
        if self.title:
            listitem_info['title'] = self.title.encode('utf-8')

        listitem = xbmcgui.ListItem(self.label.encode('utf-8'))
        listitem.setInfo('video', listitem_info)

        return listitem
        # listitem.setArt (poster, ?)
        # listitem.setLabel2 # how is this ever used? Label itself is only used as a last-ditch bit of info when nothing else is available

    @property
    def label(self):
        # label formatting is interesting, and should maybe be left up to something else
        if self.title:
            return self.title
        else:
            return self.kodi_label

    @property
    def mistyped(self):
        return not self.kodi_type == 'movie'
