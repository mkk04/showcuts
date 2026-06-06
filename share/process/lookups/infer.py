'''
Best-effort recognition of unknown / newly-released Shortcut actions.

Apple adds new actions (and third-party apps donate their own) far faster
than this project can hand-code each one. Rather than rendering every
unrecognised action as a generic "Action Under Construction" block, this
module derives a human-readable name, category and glyph straight from the
action's identifier so that *future* actions are still recognised at a basic
level without any code changes.
'''

import re

#: Identifier prefix shared by all first-party Shortcuts actions.
WF_PREFIX = 'is.workflow.actions.'

#: Friendly names for bundle / framework segments seen in app-donated
#: ("app intent") action identifiers such as
#: ``com.apple.mobiletimer-framework.MobileTimerIntents.MTToggleTimerIntent``.
APP_SEGMENTS = {
    'mobiletimer-framework': 'Clock',
    'MobileTimerIntents': 'Clock',
    'mobilecal': 'Calendar',
    'mobilenotes': 'Notes',
    'mobilesafari': 'Safari',
    'MobileSMS': 'Messages',
    'mobilemail': 'Mail',
    'mobileslideshow': 'Photos',
    'camera': 'Camera',
    'reminderkit': 'Reminders',
    'reminders': 'Reminders',
    'AccessibilityUtilities': 'Accessibility',
    'Health': 'Health',
    'weather': 'Weather',
    'Maps': 'Maps',
    'podcasts': 'Podcasts',
    'Music': 'Music',
    'iTunesStore': 'App Store',
    'TVRemoteUIService': 'Apple TV',
    'Home': 'Home',
    'findmy': 'Find My',
    'translate': 'Translate',
    'shortcuts': 'Shortcuts',
}

#: Tokens that should stay fully upper-cased instead of being title-cased.
_ACRONYMS = {
    'url', 'urls', 'ip', 'id', 'uuid', 'ssh', 'rss', 'pdf', 'html', 'css',
    'js', 'qr', 'gif', 'tv', 'dnd', 'os', 'sms', 'http', 'https', 'api',
    'json', 'xml', 'csv', 'ai', 'ml', 'ar', 'vr', 'hdr', 'usb', 'wifi',
}

#: camelCase / PascalCase boundary (a lowercase/digit followed by an uppercase).
_CAMEL_RE = re.compile(r'(?<=[a-z0-9])(?=[A-Z])')

#: Vocabulary used to split first-party identifiers, whose words are jammed
#: together in lowercase (e.g. ``getbatterylevel`` -> "Get Battery Level").
#: Greedy longest-match means plural / longer forms must precede their stems.
_VOCAB = {
    # verbs
    'get', 'set', 'show', 'open', 'create', 'add', 'remove', 'delete', 'make',
    'play', 'pause', 'stop', 'start', 'toggle', 'choose', 'select', 'find',
    'save', 'run', 'send', 'take', 'record', 'scan', 'split', 'combine',
    'replace', 'count', 'format', 'detect', 'convert', 'encode', 'decode',
    'filter', 'update', 'append', 'clear', 'copy', 'paste', 'speak',
    'translate', 'search', 'download', 'upload', 'share', 'print', 'round',
    'calculate', 'generate', 'extract', 'expand', 'match', 'adjust', 'wait',
    'repeat', 'exit', 'ask', 'log', 'export', 'import', 'dismiss', 'enable',
    'disable', 'turn', 'mute', 'dial', 'call', 'email', 'message', 'post',
    'fetch', 'load', 'close', 'quit', 'launch', 'connect', 'mount', 'zip',
    'unzip', 'hash', 'trim', 'crop', 'resize', 'rotate', 'flip', 'merge',
    'reverse', 'sort', 'shuffle', 'view', 'edit', 'new', 'preview', 'overwrite',
    # nouns (plurals before singulars for greedy matching)
    'texts', 'text', 'numbers', 'number', 'dates', 'date', 'times', 'time',
    'urls', 'url', 'links', 'link', 'images', 'image', 'photos', 'photo',
    'videos', 'video', 'files', 'file', 'folders', 'folder', 'clipboard',
    'variables', 'variable', 'items', 'item', 'lists', 'list', 'dictionary',
    'values', 'value', 'keys', 'key', 'apps', 'app', 'device', 'battery',
    'level', 'brightness', 'torch', 'flashlight', 'wifi', 'bluetooth',
    'airplane', 'mode', 'cellular', 'data', 'locations', 'location', 'weather',
    'maps', 'map', 'music', 'songs', 'song', 'playlists', 'playlist',
    'podcasts', 'podcast', 'contacts', 'contact', 'phone', 'addresses',
    'address', 'notes', 'note', 'reminders', 'reminder', 'events', 'event',
    'calendar', 'alarms', 'alarm', 'timer', 'health', 'samples', 'sample',
    'workout', 'steps', 'step', 'distance', 'web', 'pages', 'page', 'articles',
    'article', 'feeds', 'feed', 'rss', 'barcode', 'pdf', 'markdown', 'html',
    'richtext', 'rich', 'language', 'definition', 'emoji', 'names', 'name',
    'types', 'type', 'group', 'index', 'pattern', 'case', 'sound', 'alert',
    'results', 'result', 'input', 'output', 'content', 'menu', 'network',
    'details', 'ip', 'ssh', 'script', 'screen', 'screenshot', 'wallpaper',
    'volume', 'size', 'half', 'way', 'point', 'directions', 'direction',
    'travel', 'current', 'latest', 'between', 'from', 'with', 'over', 'each',
    'my', 'last', 'all',
}

#: Vocabulary sorted longest-first so greedy matching prefers longer words.
_VOCAB_SORTED = sorted(_VOCAB, key=len, reverse=True)


def _segment(blob: str):
    '''Greedily split a jammed lowercase ``blob`` using ``_VOCAB``.

    Returns the list of recognised words, or ``None`` if the blob cannot be
    fully segmented (in which case the caller keeps it verbatim).
    '''
    words = []
    i, n = 0, len(blob)
    while i < n:
        for w in _VOCAB_SORTED:
            if blob.startswith(w, i):
                words.append(w)
                i += len(w)
                break
        else:
            return None
    return words


def _split(token: str) -> [str]:
    '''Split a token on camelCase boundaries and on ``. _ -`` separators.'''
    token = _CAMEL_RE.sub(' ', token)
    return [t for t in re.split(r'[\s._\-]+', token) if t]


def _titleize(words: [str]) -> str:
    '''Title-case a list of words, preserving known acronyms.'''
    out = []
    for w in words:
        if w.lower() in _ACRONYMS:
            out.append(w.upper())
        elif w.isupper() and len(w) > 1:
            out.append(w)  # already an acronym (e.g. "AX", "MT")
        else:
            out.append(w[:1].upper() + w[1:])
    return ' '.join(out)


def humanize(identifier: str) -> str:
    '''Return a best-effort human-readable name for an action ``identifier``.'''
    if not identifier:
        return 'Unknown Action'

    if identifier.startswith(WF_PREFIX):
        remainder = identifier[len(WF_PREFIX):]
        words = []
        for piece in _split(remainder):
            if piece.islower() and len(piece) > 3:
                words.extend(_segment(piece) or [piece])
            else:
                words.append(piece)
        return _titleize(words) or 'Unknown Action'

    # App-donated intent, e.g. com.vendor.app.DoSomethingIntent
    segments = identifier.split('.')
    last = segments[-1] if segments else identifier
    last = re.sub(r'Intent$', '', last)          # drop trailing "Intent"
    last = re.sub(r'^(MT|AX|IN|SF)(?=[A-Z])', '', last)  # drop framework prefixes
    name = _titleize(_split(last))

    app = next((APP_SEGMENTS[s] for s in segments if s in APP_SEGMENTS), None)
    if app and name:
        return f'{name} ({app})'
    return name or app or identifier


def infer_action(identifier: str) -> dict:
    '''Infer a display ``name``, ``category`` and ``glyph`` from an identifier.

    Used by the fallback action so that unrecognised actions still render
    meaningfully instead of as a blank "under construction" placeholder.
    '''
    name = humanize(identifier)

    if identifier.startswith(WF_PREFIX):
        return {
            'name': name,
            'category': 'SHORTCUTS',
            'glyph': 'Magic.svg',
            'identifier': identifier,
        }

    segments = identifier.split('.')
    app = next((APP_SEGMENTS[s] for s in segments if s in APP_SEGMENTS), None)
    return {
        'name': name,
        'category': (app or 'APP').upper(),
        'glyph': 'App.svg',
        'identifier': identifier,
    }
