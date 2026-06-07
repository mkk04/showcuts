"""Build action classes at runtime from ``CustomAction`` database records.

This lets the action generator add support for new/missing action identifiers
without code changes, by turning a stored title specification into a normal
``action`` subclass that the rendering pipeline can use.
"""

from .action import action
from share.process.components._directory import text, magic, inline


def build_custom_action(custom) -> type:
    '''Return an ``action`` subclass rendering the given ``CustomAction``.'''
    title = []
    for seg in (custom.title_spec or []):
        kind = (seg or {}).get('type')
        if kind == 'text' and seg.get('value'):
            title.append(text(seg['value']))
        elif kind in ('magic', 'field') and seg.get('key'):
            title.append(magic(
                seg['key'],
                blank_text=seg.get('blank') or 'Input',
                ask_each_time=None,
            ))
        elif kind == 'inline' and seg.get('key'):
            title.append(inline(
                seg['key'],
                blank_text=seg.get('blank') or 'Text',
                ask_each_time=None,
            ))

    return type('CustomAction_dynamic', (action,), {
        'name': custom.name,
        'category': (custom.category or 'SHORTCUTS').upper(),
        'glyph': custom.glyph or 'Magic.svg',
        'result': custom.result or None,
        'title': title,
        'lines': [],
        'items': [],
    })
