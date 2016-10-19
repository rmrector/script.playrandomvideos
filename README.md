# Play Random Videos
A Kodi add-on to quickly play random videos from (nearly) any list. This add-on can
play random episodes from TV shows, movies from genres/sets/years/tags, and videos
from playlists, filesystems, and just about anything else, other than plugins.

It adds a context item to most playable lists when navigating videos, and also provides a script
that can be executed by skins with `RunScript` and JSON-RPC with `Addons.ExecuteAddon`.

## Settings
There are add-on settings to set a (un)watched filter for different video library sections.

## Skin usage
Skins can use it with an action like so: `RunScript(script.playrandomvideos, <list path>,
"label=<list label>")`.

List path is the path to the list to play, like ListItem.FolderPath, which should be
escaped (`$ESCINFO[]`). *label* is the list name, like
ListItem.Label, and is required when available, also escaped/quoted. There are optional
arguments *watchmode*, which can override the default watch mode selected in the add-on settings,
and *singlevideo* to play just a single video, if you have occasion for such an action.

In **MyVideoNav.xml** an action like `RunScript(script.playrandomvideos, "$INFO[Container.FolderPath]",
"label=$INFO[Container.FolderName]", watchmode=$INFO[Control.GetLabel(10)])`
makes for a good button in the sidebar or as some other container-focused option. Use
`<visible>!IsEmpty(Container.FolderPath) + !SubString(Container.FolderPath, plugin, left) +
!SubString(Container.FolderPath, addons, Left) + !SubString(Container.FolderPath, sources, Left)</visible>`
to hide it for paths that the script ignores.

A label is available with `$ADDON[script.playrandomvideos 32100]`, 'Play Random'.

*watchmode* accepts 'Unwatched', 'Watched', and 'Ask me', as well
as their localized equivalents with these IDs: `16101`, `16102`, and `36521`.
In **MyVideoNav.xml**, `watchmode=$INFO[Control.GetLabel(10)]` should
match the behavior of the button that switches between watched/unwatched/all,
if it is on your window. *singlevideo* needs no value, just add `singlevideo` as an argument.

## Plugins
It doesn't work for plugin paths :(. I would like it to, but I can't figure a good
way to implement it, considering all the things plugins do.
