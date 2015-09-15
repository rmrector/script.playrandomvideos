import json
import os
import xbmc
import xbmcaddon

def execute_jsonrpc(jsonrpc_command):
    if isinstance(jsonrpc_command, dict):
        jsonrpc_command = json.dumps(jsonrpc_command, ensure_ascii=False)
        if isinstance(jsonrpc_command, unicode):
            jsonrpc_command = jsonrpc_command.encode('utf-8')

    json_result = xbmc.executeJSONRPC(jsonrpc_command)
    return _json_to_str(json.loads(json_result))

def get_base_json_request(method):
    return {'jsonrpc': '2.0', 'method': method, 'params': {}, 'id': 1}

def log(message, level=xbmc.LOGDEBUG):
    if level < xbmc.LOGNOTICE:
        return
    addonid = xbmcaddon.Addon().getAddonInfo('id')

    if isinstance(message, (dict, list, tuple)):
        message = json.dumps(message, skipkeys=True, ensure_ascii=False, indent=2, cls=LogJSONEncoder)
        if isinstance(message, unicode):
            message = message.encode('utf-8')
    elif isinstance(message, unicode):
        message = message.encode('utf-8')
    elif not isinstance(message, str):
        message = str(message)

    file_message = '[%s] %s' % (addonid, message)
    xbmc.log(file_message, level)

def _json_to_str(jsoninput):
    if isinstance(jsoninput, dict):
        return {_json_to_str(key): _json_to_str(value) for key, value in jsoninput.iteritems()}
    elif isinstance(jsoninput, list):
        return [_json_to_str(item) for item in jsoninput]
    elif isinstance(jsoninput, unicode):
        return jsoninput.encode('utf-8')
    else:
        return jsoninput

class LogJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, tuple):
            return list(obj)
        # switch this to isinstance collections.Mapping (make dict) and collections.Iterable (make list)
        elif hasattr(obj, 'keys'):
            return dict((key, obj[key]) for key in obj.keys())
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
