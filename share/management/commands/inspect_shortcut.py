"""Inspect a Shortcut and report which actions are (not) recognised.

Run on a host that can reach iCloud (e.g. your Render instance):

    python manage.py inspect_shortcut https://www.icloud.com/shortcuts/<id>

For every action it prints the identifier, whether a hand-coded definition
exists, and — for unrecognised actions — the parameter keys/values. Paste the
output when asking for new actions to be added so they can be built accurately.
"""

import json
import re

import plistlib
import requests
from django.core.management.base import BaseCommand, CommandError

from share.process.entry import request_details
from share.process.sc_action.directory import categorize_action
from share.process.lookups.placeholder import NOT_IMPLEMENTED_ACTION


class Command(BaseCommand):
    help = 'Downloads a Shortcut and lists recognised / unrecognised actions.'

    def add_arguments(self, parser):
        parser.add_argument('url', help='iCloud Shortcut link or 32-char ID.')
        parser.add_argument(
            '--params', action='store_true',
            help='Also dump full parameters for unrecognised actions.',
        )

    def handle(self, *args, **options):
        try:
            _id = re.findall(r'[0-9a-f]{32}', options['url'])[0]
        except IndexError:
            raise CommandError('Could not find a 32-character Shortcut ID in the input.')

        details = request_details(_id)
        content = requests.get(details['download_link'], timeout=30).content
        actions = plistlib.loads(content).get('WFWorkflowActions', [])

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"{details['name']} — {len(actions)} action(s)"
        ))

        unknown = []
        for idx, action in enumerate(actions):
            identifier = action.get('WFWorkflowActionIdentifier', '')
            params = {k: v for k, v in action.get('WFWorkflowActionParameters', {}).items() if k != 'UUID'}
            recognised = categorize_action(identifier) is not NOT_IMPLEMENTED_ACTION

            mark = self.style.SUCCESS('  ok ') if recognised else self.style.ERROR('MISS ')
            keys = ', '.join(sorted(params)) or '-'
            self.stdout.write(f'{mark}{idx:>3}  {identifier}')
            self.stdout.write(f'           params: {keys}')
            if not recognised:
                unknown.append((idx, identifier, params))

        if unknown:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'{len(unknown)} unrecognised action(s):'))
            for idx, identifier, params in unknown:
                self.stdout.write(f'  - {identifier}')
                if options['params']:
                    dump = json.dumps(params, indent=2, default=_jsonable)
                    self.stdout.write(_indent(dump, 6))
        else:
            self.stdout.write(self.style.SUCCESS('\nAll actions are recognised.'))


def _jsonable(obj):
    if isinstance(obj, bytes):
        return f'<{len(obj)} bytes>'
    return str(obj)


def _indent(text: str, spaces: int) -> str:
    pad = ' ' * spaces
    return '\n'.join(pad + line for line in text.splitlines())
