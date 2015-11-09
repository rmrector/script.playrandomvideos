# Play Random Videos
A Kodi add-on to play random videos. This script can select and play random episodes from TV shows, movies from genres/sets/years/tags, and videos from playlists, the filesystem, and just about anything else, other than plugins. Try the Context item "Play Random Video" add-on for quick access from the context menu.

### Setting default watched filters
There are add-on settings to set the default watched filter for each video library section 'movies'/'TV shows'/'music videos', and the available options are 'all videos', only 'unwatched', only 'watched', and 'ask me', which prompts you each time the script is run.

## Skin usage
Skins can use it with an action like so: `RunScript(script.playrandomvideos, "<list path>", "label=<list label>", limit=10, forcewatchmode=<watchedmode>)`.

List path is the path to the list to play, like ListItem.FolderPath, which should be escaped (`$ESCINFO[]`) or wrapped in quotation marks. *label* is the list name, like ListItem.Label, and is required for TV Show actor/studio/tag lists, but should always be passed in when available, also escaped/quoted. *limit* is the number of videos to queue up and is optional, defaulting to a single video. *forcewatchmode* is optional and overrides the default watch mode selected in the add-on settings.

In **MyVideoNav.xml** an action like `RunScript(script.playrandomvideos, "$INFO[Container.FolderPath]", "label=$INFO[Container.FolderName]", forcewatchmode=$INFO[Control.GetLabel(10)], limit=50)` makes for a good button in the sidebar.

Get a label for your button with `$ADDON[script.playrandomvideos 32100]`, and something like `<visible>!SubString(Container.FolderPath, plugin, left) + !SubString(Container.FolderPath, addons, Left) + !SubString(Container.FolderPath, sources, Left)</visible>` hides it for paths that the script ignores.

### forcewatchmode values
*forcewatchmode* accepts 'All videos'/'Unwatched'/'Watched', as well as their localized equivalents with these IDs: `16100`, `16101`, `16102`. It also accepts 'ask me' if you want to force a prompt. In **MyVideoNav.xml**, `forcewatchmode=$INFO[Control.GetLabel(10)]` should always match the behavior of the script to the button that switches between the three, if it is on your window.

## Other bits
It doesn't work for plugin paths. I would like it to, but I can't figure a good way to implement it, considering all the things plugins do. I'm open to suggestions.

Other than the watched filter, it doesn't pay attention to list filters, such as by rating. I have ideas for hooking that up, though.
