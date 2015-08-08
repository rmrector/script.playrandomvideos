import json
import xbmcgui

class Episode(object):
    def __init__(self, episode_json):
        self.kodi_label = episode_json.get('label')
        self.episode_id = episode_json.get('id', None)
        self.tvshow_id = episode_json.get('tvshowid', None)
        self.file = episode_json.get('file')
        self.season = episode_json.get('season', None)
        self.episode = episode_json.get('episode', None)
        self.title = episode_json.get('title', None)
        self.show_title = episode_json.get('showtitle', None)

        self.kodi_type = episode_json.get('type', None)

    @property
    def listitem(self):
        """Build a Kodi ListItem that can be added to a "playlist" (Kodi play queue in python, not a real playlist) from this Episode"""
        listitem_info = {}
        if self.episode:
            listitem_info['episode'] = self.episode
        if self.season:
            listitem_info['season'] = self.season
        if self.title:
            listitem_info['title'] = self.title.encode('utf-8')
        if self.show_title:
            listitem_info['tvshowtitle'] = self.show_title

        listitem = xbmcgui.ListItem(self.label)
        listitem.setInfo('video', listitem_info)

        return listitem
        # listitem.setArt (thumb, or the following from the tv show: poster?, banner?, clearart?, clearlogo?, landscape?)
        # listitem.setLabel2 # how is this ever used? Label itself is only used as a last-ditch bit of info when nothing else is available

    @property
    def label(self):
        # label formatting is interesting, and should maybe be left up to something else
        if self.title and self.show_title:
            se_label = ''
            if self.season and self.episode:
                se_label = '{}x{} '.format(self.season, self.episode)
            return '{show_title} - {se_label}{title}'.format(show_title=self.show_title, se_label=se_label, title=self.title)
        else:
            return self.kodi_label

    @property
    def mistyped(self):
        return not self.kodi_type == 'episode'
