import xbmcaddon
import xbmcgui

import quickjson
from pykodi import localize as L
from player import get_player
from generators import get_generator

SELECTWATCHMODE_HEADING = 32010
WATCHMODE_ALLVIDEOS_TEXT = 16100
WATCHMODE_UNWATCHED_TEXT = 16101
WATCHMODE_WATCHED_TEXT = 16102
WATCHMODE_ASKME_TEXT = 36521
ADD_SOURCE_HEADER = 32011
ADD_SOURCE_MESSAGE = 32012

WATCHMODE_ALLVIDEOS = 'all videos'
WATCHMODE_UNWATCHED = 'unwatched'
WATCHMODE_WATCHED = 'watched'
WATCHMODE_ASKME = 'ask me'
# Same order as settings
WATCHMODES = (WATCHMODE_ALLVIDEOS, WATCHMODE_UNWATCHED, WATCHMODE_WATCHED, WATCHMODE_ASKME)
WATCHMODE_NONE = 'none'

pathcategory_lookup = {
    'genres': 'genre',
    'years': 'year',
    'actors': 'actor',
    'studios': 'studio',
    'tags': 'tag',
    'directors': 'director',
    'sets': 'set',
    'countries': 'country',
    'artists': 'artist',
    'albums': 'album'}

unplayed_filter = {'field': 'playcount', 'operator': 'is', 'value': '0'}
played_filter = {'field': 'playcount', 'operator': 'greaterthan', 'value': '0'}

def play(pathinfo):
    content, info = _parse_path(pathinfo)
    if not content:
        return
    singlevideo = pathinfo.get('singlevideo', False)
    try:
        get_player(get_generator(content, info), singlevideo).run()
    except quickjson.JSONException as ex:
        # json_result['error']['code'] == -32602 seems to be the generic code for "cannot access file"
        if content == 'other' and ex.json_result.get('error', {}).get('code', 0) == -32602 \
                and not any(1 for source in quickjson.get_sources('video') if info['path'].startswith(source['file'])):
            xbmcgui.Dialog().ok(L(ADD_SOURCE_HEADER), L(ADD_SOURCE_MESSAGE).format(info['path']))
        else:
            raise

def _parse_path(pathinfo):
    content = None
    skip_path = False
    result = {}
    filters = []
    if pathinfo['type'] == 'videodb':
        path_len = len(pathinfo['path'])
        firstpath = pathinfo['path'][0] if path_len else None
        if path_len > 1:
            category = pathinfo['path'][1]
            if firstpath == 'tvshows':
                content = firstpath
                if category == 'titles' and path_len <= 2:
                    # 'xsp' 'rules' are passed from library xml files, like inprogressshows.xml
                    if _has_xsprules(pathinfo):
                        filters.append({'field': 'tvshow', 'operator': 'is', 'value': [series['label'] for
                            series in quickjson.get_tvshows(pathinfo['query']['xsp']['rules'])]})
                elif category == 'titles' or path_len > 3:
                    # points to specific show, disregard any series filter
                    i = 3 if category != 'titles' else 2
                    if path_len > i:
                        result['tvshowid'] = int(pathinfo['path'][i])
                    if path_len > i + 1:
                        season = int(pathinfo['path'][i + 1])
                        if season >= 0:
                            result['season'] = season
                elif path_len > 2:
                    # contains series filter criteria
                    value = pathinfo.get('label', pathinfo['path'][2])
                    seriesfilter = _filter_from_path(category, value)
                    filters.append({'field': 'tvshow', 'operator': 'is', 'value':
                        [series['label'] for series in quickjson.get_tvshows(seriesfilter)]})
            elif firstpath in ('movies', 'musicvideos'):
                content = firstpath
                if category == 'titles' and path_len <= 2:
                    if _has_xsprules(pathinfo):
                        filters.append(pathinfo['query']['xsp']['rules'])
                if category != 'titles' and path_len > 2:
                    value = pathinfo.get('label', pathinfo['path'][2])
                    filters.append(_filter_from_path(category, value))
        elif firstpath == 'inprogresstvshows': # added in Krypton
            content = 'tvshows'
            filters.append({'field': 'tvshow', 'operator': 'is', 'value': [series['label'] for series
                in quickjson.get_tvshows({'field': 'inprogress', 'operator':'true', 'value':''})]})
    elif pathinfo['type'] == 'library':
        # TODO: read these from the actual XML files?
        if pathinfo['path'][1] == 'inprogressshows.xml':
            content = 'tvshows'
            filters.append({'field': 'tvshow', 'operator': 'is', 'value': [series['label'] for series
                in quickjson.get_tvshows({'field': 'inprogress', 'operator':'true', 'value':''})]})
        elif pathinfo['path'][1] == 'tvshows':
            content = 'tvshows'
        elif pathinfo['path'][1] == 'movies':
            content = 'movies'
        elif pathinfo['path'][1] == 'musicvideos':
            content = 'musicvideos'
        elif pathinfo['path'][1] in ('files.xml', 'playlists.xml', 'addons.xml'):
            skip_path = True
    elif pathinfo['type'] == 'special':
        if pathinfo['path'][0] == 'videoplaylists':
            skip_path = True

    if skip_path:
        return None, None

    if not content:
        content = 'other'
        result['path'] = pathinfo['full path']

    # DEPRECATED: forcewatchmode is deprecated in 1.1.0
    watchmode = _get_watchmode(pathinfo.get('watchmode') or pathinfo.get('forcewatchmode'), content)
    result['watchmode'] = watchmode
    if watchmode == WATCHMODE_NONE:
        return None, None
    if watchmode == WATCHMODE_UNWATCHED:
        filters.append(unplayed_filter)
    elif watchmode == WATCHMODE_WATCHED:
        filters.append(played_filter)

    if filters:
        result['filters'] = filters
    return (content, result)

def _filter_from_path(category, value):
    return {'field': pathcategory_lookup.get(category, category), 'operator': 'is', 'value': value}

def _has_xsprules(pathinfo):
    return 'query' in pathinfo and 'xsp' in pathinfo['query'] and 'rules' in pathinfo['query']['xsp']

def _get_watchmode(pathwatchmode, content):
    watchmode = None
    if pathwatchmode:
        # skip 'all videos' from path, prefer add-on settings
        if pathwatchmode.lower() in (WATCHMODE_UNWATCHED, WATCHMODE_WATCHED, WATCHMODE_ASKME):
            watchmode = pathwatchmode.lower()
        elif pathwatchmode == L(WATCHMODE_UNWATCHED_TEXT):
            watchmode = WATCHMODE_UNWATCHED
        elif pathwatchmode == L(WATCHMODE_WATCHED_TEXT):
            watchmode = WATCHMODE_WATCHED
        elif pathwatchmode == L(WATCHMODE_ASKME_TEXT):
            watchmode = WATCHMODE_ASKME

    if not watchmode:
        settingenum = None
        addon = xbmcaddon.Addon()
        if content == 'movies':
            settingenum = addon.getSetting('watchmodemovies')
        elif content == 'tvshows':
            settingenum = addon.getSetting('watchmodetvshows')
        elif content == 'musicvideos':
            settingenum = addon.getSetting('watchmodemusicvideos')
        elif content == 'other':
            settingenum = addon.getSetting('watchmodeother')

        if settingenum:
            try:
                watchmode = WATCHMODES[int(settingenum)]
            except ValueError:
                pass

    if watchmode == WATCHMODE_ASKME:
        return _ask_me()
    elif watchmode:
        return watchmode
    else:
        return WATCHMODE_ALLVIDEOS

def _ask_me():
    options = [L(WATCHMODE_ALLVIDEOS_TEXT), L(WATCHMODE_UNWATCHED_TEXT), L(WATCHMODE_WATCHED_TEXT)]
    selectedindex = xbmcgui.Dialog().select(L(SELECTWATCHMODE_HEADING), options)

    if selectedindex == 0:
        return WATCHMODE_ALLVIDEOS
    elif selectedindex == 1:
        return WATCHMODE_UNWATCHED
    elif selectedindex == 2:
        return WATCHMODE_WATCHED
    else:
        return WATCHMODE_NONE
