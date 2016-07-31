import xbmc

import pykodi
from pykodi import json, log

def get_tvshows(seriesfilter=None):
    json_request = get_base_json_request('VideoLibrary.GetTVShows')
    if seriesfilter:
        json_request['params']['filter'] = seriesfilter

    json_result = pykodi.execute_jsonrpc(json_request)
    if _check_json_result(json_result, 'tvshows', json_request):
        return json_result['result']['tvshows']
    else:
        return []

def get_random_episodes(tvshow_id=None, season=None, filters=None, limit=None):
    json_request = get_base_json_request('VideoLibrary.GetEpisodes')
    if tvshow_id:
        json_request['params']['tvshowid'] = tvshow_id
        if season is not None:
            json_request['params']['season'] = season
    json_request['params']['sort'] = {'method': 'random'}
    json_request['params']['properties'] = ['file', 'title', 'lastplayed',
        'episode', 'season', 'plot', 'art', 'playcount', 'runtime', 'tvshowid',
        'uniqueid', 'showtitle']
    if limit:
        json_request['params']['limits'] = {'end': limit}

    if filters:
        json_request['params']['filter'] = filter_and(*filters)

    json_result = pykodi.execute_jsonrpc(json_request)
    if _check_json_result(json_result, 'episodes', json_request):
        return json_result['result']['episodes']
    else:
        return []

def get_random_movies(filters=None, limit=None):
    json_request = get_base_json_request('VideoLibrary.GetMovies')
    json_request['params']['sort'] = {'method': 'random'}
    json_request['params']['properties'] = ['file', 'title', 'genre', 'year', 'rating',
        'playcount', 'runtime', 'lastplayed', 'plot', 'art', 'mpaa', 'imdbnumber',
        'plotoutline', 'tagline']
    if limit:
        json_request['params']['limits'] = {'end': limit}

    if filters:
        json_request['params']['filter'] = filter_and(*filters)

    json_result = pykodi.execute_jsonrpc(json_request)
    if _check_json_result(json_result, 'movies', json_request):
        return json_result['result']['movies']
    else:
        return []

def get_random_musicvideos(filters=None, limit=None):
    json_request = get_base_json_request('VideoLibrary.GetMusicVideos')
    json_request['params']['sort'] = {'method': 'random'}
    json_request['params']['properties'] = ['file', 'art', 'genre', 'lastplayed']
    if limit:
        json_request['params']['limits'] = {'end': limit}

    if filters:
        json_request['params']['filter'] = filter_and(*filters)

    json_result = pykodi.execute_jsonrpc(json_request)
    if _check_json_result(json_result, 'musicvideos', json_request):
        return json_result['result']['musicvideos']
    else:
        return []

def get_directory(path, limit=None):
    json_request = get_base_json_request('Files.GetDirectory')
    json_request['params'] = {'directory': path}
    json_request['params']['media'] = 'video'
    json_request['params']['sort'] = {'method': 'random'}
    json_request['params']['properties'] = ['mimetype', 'playcount', 'lastplayed', 'art',
        'episode', 'season', 'plot', 'runtime', 'tvshowid', 'uniqueid', 'showtitle', 'genre',
        'year', 'rating', 'mpaa', 'imdbnumber', 'plotoutline', 'tagline']
    if limit:
        json_request['params']['limits'] = {'end': limit}

    json_result = pykodi.execute_jsonrpc(json_request)
    if _check_json_result(json_result, 'files', json_request):
        return json_result['result']['files']
    else:
        return []

def remove_from_playlist(index, playlistid=xbmc.PLAYLIST_VIDEO):
    json_request = get_base_json_request('Playlist.Remove')
    json_request['params']['position'] = index
    json_request['params']['playlistid'] = playlistid

    json_result = pykodi.execute_jsonrpc(json_request)
    if not _check_json_result(json_result, 'OK', json_request):
        log(json_result)

def get_base_json_request(method):
    return {'jsonrpc': '2.0', 'method': method, 'params': {}, 'id': 1}

def filter_and(*operator_args):
    filters = [arg for arg in operator_args if arg]
    if not filters:
        return None
    if len(filters) == 1:
        return filters[0]
    return {'and': filters}

def _check_json_result(json_result, result_key, json_request):
    if 'error' in json_result:
        raise JSONException(json_request, json_result)

    return 'result' in json_result and (not result_key or result_key in json_result['result'])

class JSONException(Exception):
    def __init__(self, json_request, json_result):
        self.json_request = json_request
        self.json_result = json_result

        message = "There was an error with a JSON-RPC request.\nRequest: "
        message += json.dumps(json_request, cls=pykodi.LogJSONEncoder)
        message += "\nResult: "
        message += json.dumps(json_result, cls=pykodi.LogJSONEncoder)

        super(JSONException, self).__init__(message)
