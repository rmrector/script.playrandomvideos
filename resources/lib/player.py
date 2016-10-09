import xbmc

from listitembuilder import build_video_listitem
import quickjson
from pykodi import log

EXTEND_WHEN = 3 # Add more items when there are only X left
EXTEND_BY = 5
REMOVE_OLDER_THAN = 4 # Keep only X previously played

def get_player(source):
    result = ChunkPlayer()
    result.source = source
    return result

class ChunkPlayer(xbmc.Player):
    def __init__(self):
        super(ChunkPlayer, self).__init__()
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.playlist.clear()
        self._source = None
        self.source_exhausted = True

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self._source = source
        if source:
            self.source_exhausted = False

    def run(self):
        if self.extend_playlist():
            self.play(self.playlist)
        loopbuffer = 0
        while self.isPlaying() or loopbuffer < 2:
            if self.source_exhausted:
                break
            xbmc.sleep(2000)
            loopbuffer = 0 if self.isPlaying() else (loopbuffer + 1)
        log("I'm done", xbmc.LOGNOTICE)

    def add_to_playlist(self, item):
        self.playlist.add(item.get('file'), build_video_listitem(item))

    def extend_playlist(self):
        if self.source_exhausted:
            return False
        count = 0
        for item in self._source:
            self.add_to_playlist(item)
            count += 1
            if count >= EXTEND_BY:
                break
        self.source_exhausted = count < EXTEND_BY
        if (self.source_exhausted):
            log("Source has been exhausted", xbmc.LOGNOTICE)

        return True if count else False

    def onPlayBackStarted(self):
        if self.playlist.getposition() >= len(self.playlist) - 1 - EXTEND_WHEN:
            self.extend_playlist()
        if self.playlist.getposition() > REMOVE_OLDER_THAN:
            quickjson.remove_from_playlist(0)
