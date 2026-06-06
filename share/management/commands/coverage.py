## Dependency: boilerplate
from django.conf import settings
from django.core.management.base import BaseCommand

## Dependency: sys
from collections import Counter

## Dependency: local
from share.models import Shortcut


class Command(BaseCommand):
    help = (
        'Lists Shortcuts containing actions that are not yet hand-coded '
        '(shown as "inferred") or that failed to load, so you can see which '
        'action identifiers still need to be added to the lookup.'
    )

    def handle(self, *args, **kwargs):
        missing = Counter()        # identifier -> number of occurrences
        example = {}               # identifier -> a sample "<url> Action N"
        errors = []                # shortcuts whose actions failed to load

        for shortcut in Shortcut.objects.all():
            for idx, block in enumerate(shortcut.action_blocks.get('blocks', [])):
                kind, identifier = classify(block)
                if kind == 'error':
                    errors.append(f'{view_url(shortcut.iCloudID)} Action {idx + 1}')
                elif kind == 'inferred':
                    missing[identifier] += 1
                    example.setdefault(
                        identifier,
                        f'{view_url(shortcut.iCloudID)} Action {idx + 1}',
                    )

        self.stdout.write(self.style.MIGRATE_HEADING('Unrecognised actions (add these to the lookup):'))
        if not missing:
            self.stdout.write('  none — every action is recognised.')
        for identifier, count in missing.most_common():
            self.stdout.write(
                f'  {count:>4}x  {identifier}\n'
                f'         e.g. {example[identifier]}'
            )

        if errors:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'Actions that failed to load ({len(errors)}):'))
            for line in errors:
                self.stdout.write(f'  {line}')


def classify(block: dict):
    '''Return ``(kind, identifier)`` where kind is 'inferred', 'error' or ''.'''
    try:
        title = block['title'][0]
    except (KeyError, IndexError, TypeError):
        return '', None

    classes = title.get('class', [])
    if isinstance(classes, str):
        classes = [classes]

    if 'error' in classes or title.get('value') == 'Error Loading Action':
        return 'error', None
    if 'inferred' in classes:
        return 'inferred', title.get('attrs', {}).get('identifier')
    return '', None


def view_url(hxid: str) -> str:
    host = 'http://127.0.0.1:8000' if settings.DEBUG else 'https://showcuts.onrender.com'
    return f'{host}/share/view/{hxid}'
