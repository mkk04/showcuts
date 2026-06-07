"""Turn a stored Shortcut's rendered action blocks into inspection rows and a
Markdown document (handy for handing a Shortcut to an AI assistant)."""


def _block_dict(block) -> dict:
    return block if isinstance(block, dict) else getattr(block, '__dict__', {})


def _classes(elem) -> list:
    cls = (elem or {}).get('class', []) or []
    return [cls] if isinstance(cls, str) else list(cls)


def _elem_text(elem) -> str:
    '''Readable text for one title element, recursing into nested (inline) values.'''
    if not isinstance(elem, dict):
        return str(elem) if elem else ''
    if 'identifier' in _classes(elem):
        return ''  # skip the raw-identifier subtitle on inferred actions
    value = elem.get('value')
    if isinstance(value, list):  # inline-magic: a list of sub-elements
        return ' '.join(t for t in (_elem_text(c) for c in value) if t).strip()
    return str(value) if value else ''


def _title_text(title) -> str:
    parts = (_elem_text(elem) for elem in (title or []))
    return ' '.join(p for p in parts if p).strip()


def action_rows(shortcut) -> list:
    '''Return a list of dicts describing each action of ``shortcut``.'''
    rows = []
    blocks = (shortcut.action_blocks or {}).get('blocks', [])
    for idx, block in enumerate(blocks):
        d = _block_dict(block)
        title = d.get('title', [])
        first = _classes(title[0]) if title and isinstance(title[0], dict) else []

        if 'error' in first:
            status = 'error'
        elif 'inferred' in (d.get('css_class') or []):
            status = 'inferred'
        else:
            status = 'ok'

        rows.append({
            'index': idx + 1,
            'identifier': d.get('identifier', ''),
            'name': d.get('name', '') or _title_text(title),
            'title': _title_text(title),
            'category': d.get('category', ''),
            'indent': int(d.get('indent') or 0),
            'status': status,
        })
    return rows


def unrecognised(rows) -> list:
    '''Unique identifiers of actions that are not properly recognised.'''
    seen, out = set(), []
    for r in rows:
        if r['status'] != 'ok' and r['identifier'] and r['identifier'] not in seen:
            seen.add(r['identifier'])
            out.append(r['identifier'])
    return out


def to_markdown(shortcut) -> str:
    '''Render ``shortcut`` as a Markdown document.'''
    rows = action_rows(shortcut)
    missing = unrecognised(rows)

    out = [
        f'# {shortcut.name}',
        '',
        f'- iCloud: https://www.icloud.com/shortcuts/{shortcut.iCloudID}',
        f'- Total actions: {len(rows)}',
        f'- Unrecognised actions: {len(missing)}',
        '',
        '## Actions',
        '',
    ]
    for r in rows:
        indent = '    ' * min(r['indent'], 8)
        body = r['title'] or r['name'] or '(empty)'
        flag = '' if r['status'] == 'ok' else f'  _({r["status"]}: `{r["identifier"]}`)_'
        out.append(f'{indent}{r["index"]}. {body}{flag}')

    if missing:
        out += ['', '## Unrecognised action identifiers', '',
                'These have no hand-coded or custom definition yet:', '']
        out += [f'- `{ident}`' for ident in missing]

    out.append('')
    return '\n'.join(out)
